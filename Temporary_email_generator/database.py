import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

DATABASE_PATH = "temp_mail.db"


def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Users table with new columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            saw_promotion BOOLEAN DEFAULT 0,
            bonus_given BOOLEAN DEFAULT 0
        )
    ''')

    # ... rest of your existing table creation code ...

    conn.commit()
    conn.close()


def get_db():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)


def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Add new user to database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()


def update_user_activity(user_id: int):
    """Update user's last active timestamp"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET last_active = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()


def save_email_account(user_id: int, email: str, password: str, token: str, domain: str) -> int:
    """Save email account to database, return account ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO email_accounts (user_id, email, password, token, domain)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, email, password, token, domain))
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return account_id


def get_user_email_accounts(user_id: int) -> List[Dict]:
    """Get all email accounts for a user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, email, domain, created_at, is_active
        FROM email_accounts
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "email": row[1],
            "domain": row[2],
            "created_at": row[3],
            "is_active": row[4]
        }
        for row in rows
    ]


def get_active_email_account(user_id: int) -> Optional[Dict]:
    """Get the most recent active email account for a user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, email, password, token, domain
        FROM email_accounts
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "email": row[1],
            "password": row[2],
            "token": row[3],
            "domain": row[4]
        }
    return None


def get_email_account_by_id(account_id: int) -> Optional[Dict]:
    """Get email account by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, email, password, token, domain
        FROM email_accounts
        WHERE id = ? AND is_active = 1
    ''', (account_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "email": row[2],
            "password": row[3],
            "token": row[4],
            "domain": row[5]
        }
    return None


def deactivate_email_account(account_id: int):
    """Deactivate an email account"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE email_accounts SET is_active = 0
        WHERE id = ?
    ''', (account_id,))
    conn.commit()
    conn.close()


def cache_message(account_id: int, message_id: str, sender: str, subject: str, body: str, received_at: str):
    """Cache a message in database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO cached_messages 
        (email_account_id, message_id, sender, subject, body, received_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (account_id, message_id, sender, subject, body, received_at))
    conn.commit()
    conn.close()


def get_cached_messages(account_id: int, limit: int = 10) -> List[Dict]:
    """Get cached messages for an email account"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, message_id, sender, subject, body, received_at, is_read
        FROM cached_messages
        WHERE email_account_id = ?
        ORDER BY received_at DESC
        LIMIT ?
    ''', (account_id, limit))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "message_id": row[1],
            "sender": row[2],
            "subject": row[3] or "(No subject)",
            "body": row[4],
            "received_at": row[5],
            "is_read": row[6]
        }
        for row in rows
    ]


def mark_message_as_read(message_cache_id: int):
    """Mark a cached message as read"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE cached_messages SET is_read = 1
        WHERE id = ?
    ''', (message_cache_id,))
    conn.commit()
    conn.close()


def get_user_email_count(user_id: int) -> int:
    """Get count of active email accounts for a user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM email_accounts
        WHERE user_id = ? AND is_active = 1
    ''', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count