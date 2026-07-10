import sqlite3
import os
import time
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music_history.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('\n        CREATE TABLE IF NOT EXISTS listening_history (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            song_id TEXT,\n            song_name TEXT,\n            artist_name TEXT,\n            album_name TEXT,\n            duration_ms INTEGER,\n            played_at INTEGER\n        )\n    ')
    conn.commit()
    conn.close()

def log_song(song_id, song_name, artist_name, album_name, duration_ms):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('\n        SELECT song_id, played_at FROM listening_history \n        ORDER BY played_at DESC LIMIT 1\n    ')
    last_log = cursor.fetchone()
    current_time = int(time.time())
    if last_log and last_log[0] == song_id:
        last_played_at = last_log[1]
        if (current_time - last_played_at) * 1000 < duration_ms - 5000:
            conn.close()
            return False
    cursor.execute('\n        INSERT INTO listening_history (song_id, song_name, artist_name, album_name, duration_ms, played_at)\n        VALUES (?, ?, ?, ?, ?, ?)\n    ', (song_id, song_name, artist_name, album_name, duration_ms, current_time))
    conn.commit()
    conn.close()
    return True

def get_top_artist():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('\n        SELECT artist_name, COUNT(*) as play_count \n        FROM listening_history \n        GROUP BY artist_name \n        ORDER BY play_count DESC \n        LIMIT 1\n    ')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'Unknown'

def get_listening_streak():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("\n        SELECT DISTINCT date(played_at, 'unixepoch', 'localtime') \n        FROM listening_history \n        ORDER BY date(played_at, 'unixepoch', 'localtime') DESC\n    ")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return 0
    dates = [row[0] for row in rows]
    import datetime
    today = datetime.date.today()
    streak = 0
    if today.strftime('%Y-%m-%d') in dates:
        streak += 1
        current_check_date = today - datetime.timedelta(days=1)
    elif (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d') in dates:
        streak += 1
        current_check_date = today - datetime.timedelta(days=2)
    else:
        return 0
    while current_check_date.strftime('%Y-%m-%d') in dates:
        streak += 1
        current_check_date -= datetime.timedelta(days=1)
    return streak

def get_top_song():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('\n        SELECT song_name, COUNT(*) as play_count \n        FROM listening_history \n        GROUP BY song_id \n        ORDER BY play_count DESC \n        LIMIT 1\n    ')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'Unknown'

def get_total_tracks_played():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listening_history')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_total_hours_listened():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(duration_ms) FROM listening_history')
    row = cursor.fetchone()
    conn.close()
    total_ms = row[0] if row and row[0] else 0
    total_hours = total_ms / (1000 * 60 * 60)
    return round(total_hours, 2)
if __name__ == '__main__':
    init_db()
    print('Database initialized.')