import re
import os
from flask import Flask, request, render_template, redirect, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)

def extract_video_id(url):
    match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def authenticate_youtube():
    SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    return build('youtube', 'v3', credentials=creds)

def create_playlist(youtube, title, description, privacy):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
            },
            "status": {
                "privacyStatus": privacy
            }
        }
    )
    return request.execute()['id']

def add_video_to_playlist(youtube, video_id, playlist_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    request.execute()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Obtendo dados do formulário
        file = request.files['file']
        title = request.form['title']
        description = request.form['description']
        privacy = request.form['privacy']

        # Ler IDs dos vídeos do arquivo
        video_ids = []
        if file:
            content = file.read().decode('utf-8')
            video_urls = content.splitlines()
            video_ids = [extract_video_id(url) for url in video_urls]

        # Autenticar e criar a playlist
        youtube = authenticate_youtube()
        playlist_id = create_playlist(youtube, title, description, privacy)

        # Adicionar vídeos à playlist
        for video_id in video_ids:
            if video_id:
                add_video_to_playlist(youtube, video_id, playlist_id)

        return redirect(url_for('index'))

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)