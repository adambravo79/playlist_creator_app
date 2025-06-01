from flask import Flask, request, redirect, session, render_template
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import google.auth.transport.requests
import google.oauth2.credentials

app = Flask(__name__)
app.secret_key = "sua_chave_secreta"

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
REDIRECT_URI = 'http://127.0.0.1:5000/oauth2callback'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['title'] = request.form['title']
        session['description'] = request.form['description']
        session['privacy'] = request.form['privacy']
        file = request.files['file']
        session['video_urls'] = file.read().decode('utf-8').splitlines()

        # Iniciar fluxo OAuth
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        session['state'] = state
        return redirect(auth_url)

    return render_template('index.html')


@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return redirect('/create')


@app.route('/create')
def create_playlist():
    if 'credentials' not in session:
        return redirect('/')

    creds = google.oauth2.credentials.Credentials(**session['credentials'])

    youtube = build('youtube', 'v3', credentials=creds)

    try:
        # Criar playlist
        response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": session['title'],
                    "description": session['description']
                },
                "status": {
                    "privacyStatus": session['privacy']
                }
            }
        ).execute()

        playlist_id = response['id']

        # Adicionar vídeos
        for url in session['video_urls']:
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
                youtube.playlistItems().insert(
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
                ).execute()

        return render_template("sucesso.html", playlist_id=playlist_id)

    except Exception as e:
        print("Erro ao criar playlist:", e)
        if "youtubeSignupRequired" in str(e):
            return render_template("erro_canal.html")
        return f"Erro: {e}"

if __name__ == "__main__":
    app.run(port=5000, debug=True)

# if __name__ == "__main__":
#     # Rode o Flask sem o reloader automático, que causa o MismatchingStateError
#     app.run(debug=True, use_reloader=False)
