import re
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def extract_video_id(url):
    match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def authenticate_youtube():
    SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    return build('youtube', 'v3', credentials=creds)

def create_playlist(youtube, title, description):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
            },
            "status": {
                "privacyStatus": "public"
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

if __name__ == "__main__":
    youtube = authenticate_youtube()
    
    video_urls = [
        "https://www.youtube.com/watch?v=eidXyMGsUjI",
        "https://youtu.be/isVoNg_tn_k?si=_0-Vnupf3GSLUHdV",
        # Adicione mais URLs aqui
    ]
    
    video_ids = [extract_video_id(url) for url in video_urls]
    playlist_id = create_playlist(youtube, "Minha Playlist", "Descrição da Playlist")
    
    for video_id in video_ids:
        add_video_to_playlist(youtube, video_id, playlist_id)

    print("Playlist criada e vídeos adicionados!")