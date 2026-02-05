import sqlite3
import os
from datetime import datetime

# Railway serverida /app/data papkasini ishlatamiz.
# Agar lokal kompyuterda bo'lsa, shunchaki yoniga saqlaydi.
if os.path.exists("/app/data"):
    DB_PATH = "/app/data/halol_bot.db"
else:
    DB_PATH = "halol_bot.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Bazani yaratish"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_premium INTEGER DEFAULT 0,
                scans_today INTEGER DEFAULT 0,
                last_scan_date TEXT,
                total_scans INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def register_user(user_id):
    """Foydalanuvchini ro'yxatga olish"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, last_scan_date) VALUES (?, ?)", 
                       (user_id, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

def set_premium(user_id):
    """Premium berish"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
        conn.commit()

def is_premium(user_id):
    """Premium bormi?"""
    register_user(user_id) # Har ehtimolga qarshi
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False

def check_limit(user_id, limit=5):
    """Limitni tekshirish (Kunlik)"""
    register_user(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT scans_today, last_scan_date, is_premium FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row: return True # Xatolik bo'lsa ruxsat beramiz
        
        scans, last_date, is_prem = row
        
        # Agar Premium bo'lsa - limit yo'q
        if is_prem == 1:
            return False # Limit yetib kelmadi (False = limit tugamadi)

        # Agar yangi kun boshlangan bo'lsa, hisobni nolga tushiramiz
        if last_date != today:
            cursor.execute("UPDATE users SET scans_today = 0, last_scan_date = ? WHERE user_id = ?", (today, user_id))
            conn.commit()
            scans = 0
            
        return scans >= limit # Agar limitdan oshgan bo'lsa True qaytaradi

def add_scan(user_id):
    """Skanerlar sonini oshirish"""
    register_user(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        # Avval sanani tekshiramiz (kun yangilanishi uchun)
        cursor.execute("SELECT last_scan_date FROM users WHERE user_id = ?", (user_id,))
        last_date = cursor.fetchone()[0]
        
        if last_date != today:
            cursor.execute("UPDATE users SET scans_today = 1, last_scan_date = ?, total_scans = total_scans + 1 WHERE user_id = ?", (today, user_id))
        else:
            cursor.execute("UPDATE users SET scans_today = scans_today + 1, total_scans = total_scans + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

def get_stats():
    """Admin uchun statistika"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        premium_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_scans) FROM users")
        total_scans = cursor.fetchone()[0] or 0
        
        return total_users, premium_users, total_scans

def get_user_stats(user_id):
    """Foydalanuvchi o'z statistikasini ko'rishi uchun"""
    register_user(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT total_scans, is_premium, scans_today FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
