import time
import sys
import database
import spotify_api
import widget_api
POLL_INTERVAL = 10

def update_discord_widget(song_name, artist_name, album_name, cover_url):
    print(f'[*] Updating Discord widget for: {song_name}')
    listening_streak = database.get_listening_streak()
    top_song = database.get_top_song()
    total_tracks = database.get_total_tracks_played()
    total_hours = database.get_total_hours_listened()
    success = widget_api.update_music_widget(song_name=song_name, artist_name=artist_name, album_name=album_name, listening_streak=listening_streak, top_song=top_song, total_tracks=total_tracks, total_hours=total_hours, cover_url=cover_url)
    return success

def main():
    print('=======================================')
    print('   Spotify -> Discord Lifetime Tracker ')
    print('=======================================')
    database.init_db()
    try:
        sp = spotify_api.get_spotify_client()
        print('[*] Successfully connected to Spotify API!')
    except Exception as e:
        print(f'[!] Failed to connect to Spotify: {e}')
        print('[!] Make sure you filled out SPOTIPY_CLIENT_ID and SECRET in .env!')
        sys.exit(1)
    print(f'[*] Starting polling loop every {POLL_INTERVAL} seconds. Press Ctrl+C to stop.')
    print('=======================================\n')
    last_pushed_song_id = None
    while True:
        try:
            playing = spotify_api.get_currently_playing(sp)
            if playing:
                was_new_play = database.log_song(song_id=playing['song_id'], song_name=playing['song_name'], artist_name=playing['artist_name'], album_name=playing['album_name'], duration_ms=playing['duration_ms'])
                if was_new_play:
                    print(f"[+] Logged new play: {playing['song_name']} by {playing['artist_name']}")
                if last_pushed_song_id != playing['song_id']:
                    update_discord_widget(playing['song_name'], playing['artist_name'], playing['album_name'], playing.get('cover_url', ''))
                    last_pushed_song_id = playing['song_id']
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print('\n[*] Exiting Tracker...')
            sys.exit(0)
        except Exception as e:
            print(f'[!] Unexpected error in main loop: {e}')
            time.sleep(POLL_INTERVAL)
if __name__ == '__main__':
    main()