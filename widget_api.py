import requests
import time
import sys
import urllib.request
import json
import base64
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
USER_TOKEN = os.getenv('DISCORD_USER_TOKEN')
APPLICATION_ID = os.getenv('DISCORD_APPLICATION_ID')
CONFIG_ID = os.getenv('DISCORD_CONFIG_ID')
DEFAULT_COVER_ASSET = os.getenv('DEFAULT_COVER_ASSET')
URL = f'https://discord.com/api/v9/applications/{APPLICATION_ID}/widget-configs/{CONFIG_ID}'
HEADERS = {'Authorization': USER_TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

CACHE_FILE = os.path.join(os.path.dirname(__file__), '.last_asset_key')
last_asset_key = None
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        last_asset_key = f.read().strip()

def update_cover_asset(cover_url: str) -> str:
    global last_asset_key
    if not cover_url:
        return DEFAULT_COVER_ASSET
    try:
        print('[*] Downloading Spotify album cover...')
        req = urllib.request.Request(cover_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            image_bytes = response.read()
        assets_url = f'https://discord.com/api/v9/applications/{APPLICATION_ID}/assets'
        upload_req_url = f'{assets_url}/upload'
        upload_req_payload = {'filename': 'cover.jpg', 'file_size': len(image_bytes)}
        req1 = urllib.request.Request(upload_req_url, data=json.dumps(upload_req_payload).encode('utf-8'), headers=HEADERS, method='POST')
        with urllib.request.urlopen(req1) as res1:
            upload_data = json.loads(res1.read().decode())
        print('[*] Uploading image to Google Cloud Storage...')
        upload_url = upload_data['upload_url']
        upload_filename = upload_data['upload_filename']
        gcs_req = urllib.request.Request(upload_url, data=image_bytes, method='PUT')
        gcs_req.add_header('Content-Type', 'image/jpeg')
        urllib.request.urlopen(gcs_req)
        print('[*] Registering asset with Discord...')
        asset_name = f'cover_{int(time.time())}'
        register_payload = {'key': asset_name, 'upload_filename': upload_filename, 'visibility': 'public'}
        req3 = urllib.request.Request(assets_url, data=json.dumps(register_payload).encode('utf-8'), headers=HEADERS, method='POST')
        with urllib.request.urlopen(req3) as res3:
            final_asset = json.loads(res3.read().decode())
            current_asset_id = final_asset.get('asset_id')
            print(f"[+] Successfully registered asset: {asset_name} (ID: {current_asset_id})")

        if last_asset_key:
            try:
                requests.delete(f"{assets_url}/{last_asset_key}", headers=HEADERS, timeout=5)
            except Exception:
                pass
        last_asset_key = asset_name
        try:
            with open(CACHE_FILE, 'w') as f:
                f.write(last_asset_key)
        except Exception:
            pass

        return asset_name
    except Exception as e:
        print(f'[!] Failed to upload album cover: {e}')
        if hasattr(e, 'read'):
            print(f'Response Body: {e.read().decode()}')
        return DEFAULT_COVER_ASSET

def update_music_widget(song_name: str, artist_name: str, album_name: str, listening_streak: int, top_song: str, total_tracks: int, total_hours: float, cover_url: str=''):
    asset_id = update_cover_asset(cover_url)
    
    if not asset_id:
        print(f"[!] Skipping widget update for '{song_name}': No cover available and DEFAULT_COVER_ASSET is not set in .env")
        return False

    payload = {'surfaces': {'widget_top': {'layout': 'widget_top_hero', 'components': {'hero_image': {'fields': {'image': {'presentation_type': 'image', 'value_type': 'application_asset', 'value': asset_id}}}, 'title': {'fields': {'text': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': song_name}}}}}, 'widget_bottom': {'layout': 'widget_bottom_stats', 'components': {'stat_1': {'fields': {'label': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': artist_name}, 'value': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': 'Artist'}}}, 'stat_2': {'fields': {'label': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': album_name}, 'value': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': 'Album'}}}, 'stat_3': {'fields': {'label': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': str(listening_streak)}, 'value': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': 'Day Streak'}}}, 'stat_4': {'fields': {'label': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': top_song}, 'value': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': 'Top Song'}}}, 'stat_5': {'fields': {'label': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': str(total_tracks)}, 'value': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': 'Total Plays'}}}, 'stat_6': {'fields': {'label': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': str(total_hours)}, 'value': {'presentation_type': 'text', 'value_type': 'custom_string', 'value': 'Total Hours'}}}}}, 'add_widget_preview': {'layout': 'add_widget_preview_hero', 'components': {'hero_image': {'fields': {'image': {'presentation_type': 'image', 'value_type': 'application_asset', 'value': asset_id}}}}}}}

    for i in range(10):
        try:
            response = requests.patch(URL, headers=HEADERS, json=payload)
            if response.status_code == 200:
                print(f'[*] Successfully updated widget -> {song_name} by {artist_name}')
                return True
            elif response.status_code == 204:
                print(f'[*] Successfully updated widget (No Content response) -> {song_name} by {artist_name}')
                return True
            else:
                error_msg = response.text
                if 'WIDGET_CONFIG_MISSING_ASSET' in error_msg:
                    print(f"[*] Discord CDN hasn't processed the image yet. Retrying in 2s... ({i + 1}/10)")
                    time.sleep(2)
                else:
                    print(f'[!] Failed to update widget. Status: {response.status_code}')
                    print(error_msg)
                    return False
        except Exception as e:
            print(f'[!] Error updating widget: {e}')
            return False
    print('[!] Exceeded maximum retries waiting for Discord CDN.')
    return False

