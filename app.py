import base64
import io
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.join(os.getcwd(),'lib'))

import emoji
import requests
import matplotlib.pyplot as plt
import googleapiclient.discovery
import zcatalyst_sdk as zcatalyst
from googleapiclient.errors import HttpError
from flask import Flask, request, render_template
from zcatalyst_sdk.exceptions import CatalystAPIError, CatalystError


app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/processapi', methods=['POST'])
def processapi():
    yid = parse_yid(request.form['youtube_id'])
    pyid = process(yid)
    print("processfinished")
    return pyid


@app.route('/results/<pyid>', methods=['GET'])
def results_page(pyid):
    zapp = zcatalyst.initialize(req=request)
    zcql_service = zapp.zcql()
    resp = zcql_service.execute_query(f"select * from META where ROWID='{pyid}'")
    folder = zapp.filestore().folder(3171000000026001)
    echart:bytes = folder.download_file(resp[0]['META']['EFID'])
    echart_base64 = base64.b64encode(echart).decode('utf-8')
    tchart:bytes = folder.download_file(resp[0]['META']['TFID'])
    tchart_base64 = base64.b64encode(tchart).decode('utf-8')
    return render_template('results.html', pyid=pyid, echart=echart_base64, tchart=tchart_base64, yid=resp[0]['META']['YID'])


@app.route('/comments/<pyid>', methods=['GET'])
def comments_page(pyid: str):
    zapp = zcatalyst.initialize(req=request)
    zcql_service = zapp.zcql()
    eresult = zcql_service.execute_query(f"select * from EMOJICOMMENTS where yid='{pyid}'")
    tresult = zcql_service.execute_query(f"select * from TEXTCOMMENTS where yid='{pyid}'")
    return render_template('comments.html', edata=eresult, tdata=tresult)


def process(yid: str):
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
    filename = "EMOJICHART" if emoji else "TEXTCHART"
    filecolname = "EFID" if emoji else "TFID"
    sentiments_list = []
    table_service = zapp.datastore().table(tablename)
    zcql_service = zapp.zcql()
    try:
        for comment in comments_list:
            comment = truncate_sentence(comment)
            sentiment= get_sentiment_result(comment)
            sentiments_list.append(sentiment)
            row_data = {'YID': pyid, 'COMMENT': comment, 'SENTIMENT': sentiment}
            if insert:
                table_service.insert_row(row_data)
            else:
                zcql_service.execute_query(f"update {tablename} set comment = {comment}, sentiment = {sentiment} where yid='{pyid}'")
        chart_buffer = generate_pie_chart(sentiments_list)
        folder = zapp.filestore().folder(3171000000026001)
        resp = folder.upload_file(f'{pyid}-{filename}', chart_buffer)

        meta_table = zapp.datastore().table("META")
        row_data = {'ROWID': pyid, filecolname: resp['id']}
        meta_table.update_row(row_data)

    except CatalystAPIError as e:
        print(e)
    except CatalystError as e:
        print(e)


def generate_pie_chart(sentiments_list):
    total_count = len(sentiments_list)
    if total_count==0:
        return
    positive_count = sentiments_list.count('POSITIVE')
    negative_count = sentiments_list.count('NEGATIVE')
    neutral_count = sentiments_list.count('NEUTRAL')

    positive_percentage = (positive_count / total_count) * 100
    negative_percentage = (negative_count / total_count) * 100
    neutral_percentage = (neutral_count / total_count) * 100

    print("data -", positive_percentage,negative_percentage,neutral_percentage)

    labels = ['POSITIVE', 'NEGATIVE', 'NEUTRAL']
    sizes = [positive_percentage, negative_percentage, neutral_percentage]
    colors = ['lightcoral', 'lightskyblue', 'lightgreen']
    explode = (0.1, 0, 0)

    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    plt.axis('equal')
    chart = io.BytesIO()
    plt.savefig(chart, format='png')
    plt.close()

    chart.seek(0)
    chart_buffer = io.BufferedReader(chart)
    return chart_buffer
    


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

def truncate_sentence(sentence, max_length=512):
    if len(sentence) > max_length:
        truncated_sentence = sentence[:max_length]
        return truncated_sentence
    else:
        return sentence

def get_sentiment_result(comment: str):
    api_token = os.getenv('HF_KEY')
    headers = {"Authorization": f"Bearer {api_token}"}
    model_id = "nlptown/bert-base-multilingual-uncased-sentiment"
    API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
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
