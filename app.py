import os
import re
import sys
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.join(os.getcwd(),'lib'))
print(sys.path)


import emoji
import googleapiclient.discovery
import zcatalyst_sdk as zcatalyst
from googleapiclient.errors import HttpError
from flask import Flask, request, render_template, url_for
from zcatalyst_sdk.exceptions import CatalystAPIError, CatalystError


app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        yid = parse_yid(request.form['youtube_id'])
        pyid = fetch_and_store_comments(yid)
        return f'''
            <p>click here</p>
            <form method="GET" action="{url_for('comments_page', pyid=pyid)}">
                <input type="submit" value="show">
            </form>
        '''
    return render_template('index.html')

@app.route('/comments/<pyid>', methods=['GET'])
def comments_page(pyid: str):
    zapp = zcatalyst.initialize(req=request)
    zcql_service = zapp.zcql()
    eresult = zcql_service.execute_query(f"select * from EMOJICOMMENTS where yid='{pyid}'")
    tresult = zcql_service.execute_query(f"select * from TEXTCOMMENTS where yid='{pyid}'")
    return render_template('comments.html', edata=eresult, tdata=tresult)

def fetch_and_store_comments(yid: str):
    zapp = zcatalyst.initialize(req=request)
    zcql_service = zapp.zcql()
    result = zcql_service.execute_query(f"select * from META where yid='{yid}'")
    new = True
    pyid = ""

    if result:
        lastfetch = result[0]["META"]["MODIFIEDTIME"]
        pyid = result[0]["META"]["ROWID"]
        lastfetchtime = datetime.strptime(lastfetch, '%Y-%m-%d %H:%M:%S:%f')
        current_time = datetime.now()
        time_difference = current_time - lastfetchtime
        if time_difference < timedelta(days=1):
            return pyid
        new = False
        

    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=os.getenv('MY_API_KEY'))
    zapp = zcatalyst.initialize(req=request)
    comments_list = []
    try:
        results = youtube.commentThreads().list(
            part='snippet',
            videoId=yid,
            maxResults=100
        ).execute()

        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments_list.append(comment)
        
        if new:
            table_service = zapp.datastore().table("META")
            row_data = {'YID': yid}
            tresp = table_service.insert_row(row_data)
            pyid = tresp['ROWID']

        comments_with_emoji,comments_without_emoji = split_sentences_with_and_without_emoji(comments_list)
        analyse_and_store_comments(zapp, True, pyid, comments_with_emoji, new)
        analyse_and_store_comments(zapp, False, pyid, comments_without_emoji, new)
        return pyid

    except HttpError as e:
        print(e)
        return [f'An error occurred: {e}']
    except Exception as e:
        print(e)
        return [f'An unexpected error occurred: {e}']

def analyse_and_store_comments(zapp, emoji: bool, pyid: str, comments_list: list, insert: bool):
    tablename =  "EMOJICOMMENTS" if emoji else "TEXTCOMMENTS"
    try:
        for comment in comments_list:
            table_service = zapp.datastore().table(tablename)
            sentiment= get_sentiment_result(comment)
            row_data = {'YID': pyid, 'COMMENT': comment, 'SENTIMENT': sentiment}
            if insert:
                table_service.insert_row(row_data)
            else:
                table_service.update_row(row_data)
    except CatalystAPIError as e:
        print(e)
    except CatalystError as e:
        print(e)

def parse_yid(yid: str) -> str:
    if not yid.startswith(('https', 'http')):
        return yid
    parsed_url = urlparse(yid)
    return parse_qs(parsed_url.query).get('v', "")[0]

def split_sentences_with_and_without_emoji(comments_list):
    comments_with_emoji = []
    comments_without_emoji = []

    for comments in comments_list:
        if any(char in emoji.UNICODE_EMOJI['en'] for char in comments):
            comments_with_emoji.append(comments)
        else:
            comments_without_emoji.append(comments)

    return comments_with_emoji, comments_without_emoji

def get_sentiment_result(comment: str):
    api_token = os.getenv('HF_KEY')
    headers = {"Authorization": f"Bearer {api_token}"}
    API_URL = f"https://api-inference.huggingface.co/models/nlptown/bert-base-multilingual-uncased-sentiment"
    payload = { "inputs": comment}
    sentiment_result = requests.post(API_URL, headers=headers, json=payload).json()
    print(sentiment_result)
    sentiment_label = re.search(r'\d+', sentiment_result[0][0]['label']).group()
    star_rating = int(sentiment_label)

    if star_rating == 3:
        return "NEUTRAL"
    else:
        return "POSITIVE" if star_rating > 3 else "NEGATIVE"

listen_port = os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000)
app.run(host='0.0.0.0', port = listen_port)
