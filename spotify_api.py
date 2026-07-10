import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
scope = 'user-read-currently-playing'

def get_spotify_client():
    auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope, open_browser=True)
    return spotipy.Spotify(auth_manager=auth_manager)

def get_currently_playing(sp):
    try:
        current_track = sp.current_user_playing_track()
        if current_track is not None and current_track['is_playing']:
            item = current_track['item']
            if not item:
                return None
            cover_url = ''
            if 'album' in item and 'images' in item['album'] and (len(item['album']['images']) > 0):
                cover_url = item['album']['images'][0]['url']
            return {'song_id': item['id'], 'song_name': item['name'], 'artist_name': ', '.join([artist['name'] for artist in item['artists']]), 'album_name': item['album']['name'], 'duration_ms': item['duration_ms'], 'cover_url': cover_url}
    except Exception as e:
        print(f'[!] Error fetching from Spotify: {e}')
    return None
if __name__ == '__main__':
    print('Initializing Spotify Client...')
    sp = get_spotify_client()
    playing = get_currently_playing(sp)
    if playing:
        print(f"Currently playing: {playing['song_name']} by {playing['artist_name']}")
    else:
        print('Nothing is currently playing on Spotify.')