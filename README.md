# SentimentShop

## Overview

This project utilizes the Zoho Catalyst platform to perform sentiment analysis on YouTube video comments. It extracts comments from a specified YouTube video, analyzes the sentiment of each comment, and presents the results through a user interface.

## Features

- **Sentiment Analysis**: Utilizes the Hugging Face Inference API to analyze the sentiment of YouTube video comments.
  
- **Emoji and Text Comments**: Separates comments into those containing emojis and those without for more detailed analysis.
  
- **Charts and Visualizations**: Generates pie charts illustrating the distribution of positive, negative, and neutral sentiments in both emoji and text comments.

- **Caching and Updates**: Stores results in a Zoho Catalyst table to avoid redundant API calls and updates the sentiment analysis if the video comments have changed.

## Getting Started

### Prerequisites

- Python 3.x
- Zoho Catalyst Account
- Hugging Face API Key
- YouTube Data API Key

### Configuration in Zoho Catalyst

Create a project in Zoho Catalyst and create the resources as below 

1. Create Folders:

    Create a folder in your Zoho Catalyst File Store (This folder will be used to store chart files).
    
    Note: Make sure to change the given FolderID with your actual FolderID

2. Create Tables:

    Create the following tables in your Zoho Catalyst workspace:

    - META table: Used to store metadata about processed YouTube videos.
    
        Columns: YID, OSENTIMENT, EFID, TFID. (ROWID: Primary Key and MODIFIEDTIME will be created automatically while creating the table).

    - EMOJICOMMENTS: Used to store comments with emojis.
        
        Columns: YID (Foreign Key referencing META), COMMENT, SENTIMENT.

    - TEXTCOMMENTS: Used to store comments without emojis.
        
        Columns: YID (Foreign Key referencing META), COMMENT, SENTIMENT.

### Installation and Setup

1. Install Zoho Catalyst CLI:

   If you haven't installed the Zoho Catalyst CLI, you can do so by following the instructions in the [official documentation](https://docs.catalyst.zoho.com/en/getting-started/installing-catalyst-cli/).

2. Initialize and Link the Catalyst Project:

   After installing the Catalyst CLI, initialize and link the Zoho Catalyst project which we have created with resources. Replace `your_project_name` with the desired project name:

   ```bash
   catalyst init

3. After initializing, create an Catalyst AppSail

4. Clone the repository inside the created AppSail folder:

   ```bash
   git clone https://github.com/GrpProjects/SentimentAnalysisOnYoutubeComments.git

5. Set up Environmental Variables:

    Before running the application, make sure to set up the following environmental variables:

    - MY_API_KEY: Your YouTube Data API Key.
    - HF_KEY: Your Hugging Face API Key.
    - X_ZOHO_CATALYST_LISTEN_PORT (Optional): Set the Zoho Catalyst listen port, default is 9000.

    You can set these environmental variables in your local environment or through your deployment platform. For example, you can use the following commands in the terminal:

    ```bash
    export MY_API_KEY=your_youtube_api_key
    export HF_KEY=your_hugging_face_api_key

    Make sure to replace your_youtube_api_key and your_hugging_face_api_key with your actual API keys.

### Usage
1. Run the application in your local system using Catalyst Serve:

    ```bash
    catalyst serve
    ```

    - Open your web browser and navigate to the link provide right after hitting Catalyst serve
    - Enter the YouTube video ID/URL in the provided form on the homepage and submit.
    - View sentiment analysis results, charts, and comments on the results and comments pages.

### Project Structure
- app.py: Main Flask application file.
- templates/: Folder containing HTML templates for the user interface.
- static/: Folder containing static files (CSS, JS, etc.) for the user interface.
- lib/: Additional Python modules and utilities.

## Acknowledgments
- [Zoho Catalyst](https://www.zoho.com/catalyst/): Providing the robust and scalable serverless platform for running and deploying applications.
- [Hugging Face Inference API](https://huggingface.co/inference-api): Offering state-of-the-art natural language processing models and tools for sentiment analysis.
- [YouTube Data API](https://developers.google.com/youtube/v3): Enabling access to YouTube data, allowing the extraction of video 

## Live Application

- Explore the live application of the YouTube Sentiment Analysis application hosted on Zoho Catalyst:

    [SentimentShop- Live Application](https://youtubeproductreview-10068906480.development.catalystappsail.com/)

- Feel free to try it out and analyze the sentiment of YouTube video comments in real-time!

