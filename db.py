import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        # Fallback (ehtiyot shart)
        import sqlite3
        return sqlite3.connect("bot_database.db")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            is_premium BOOLEAN DEFAULT FALSE,
            daily_scans INTEGER DEFAULT 0,
            last_scan_date TEXT,
            total_scans INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()

def register_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO users (telegram_id, last_scan_date) 
        VALUES (%s, %s) 
        ON CONFLICT (telegram_id) DO NOTHING
    """, (user_id, today))
    conn.commit()
    conn.close()

def check_limit(user_id, limit):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT is_premium, daily_scans, last_scan_date FROM users WHERE telegram_id = %s", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        register_user(user_id)
        conn.close()
        return False

    is_premium, daily_scans, last_date = row
    
    if is_premium: 
        conn.close()
        return False 

    if last_date != today:
        cursor.execute("UPDATE users SET daily_scans = 0, last_scan_date = %s WHERE telegram_id = %s", (today, user_id))
        conn.commit()
        daily_scans = 0

    if daily_scans >= limit:
        conn.close()
        return True 

    conn.close()
    return False

def add_scan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET daily_scans = daily_scans + 1, total_scans = total_scans + 1 WHERE telegram_id = %s", (user_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
    premiums = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_scans) FROM users")
    res = cursor.fetchone()[0]
    scans = res if res else 0
    conn.close()
    return users, premiums, scans

def get_user_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT total_scans, is_premium, daily_scans, last_scan_date FROM users WHERE telegram_id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        total, is_prem, daily, last_date = row
        if last_date != today: daily = 0
        return total, is_prem, daily
    return None

def set_premium(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = TRUE WHERE telegram_id = %s", (user_id,))
    conn.commit()
    conn.close()

def is_premium(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_premium FROM users WHERE telegram_id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row[0]

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users