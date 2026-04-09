import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "/tmp/finance.db")

def get_connection():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role        TEXT NOT NULL CHECK(role IN ('viewer','analyst','admin')),
            status      TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive')),
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS financial_records (
            id          TEXT PRIMARY KEY,
            amount      REAL NOT NULL CHECK(amount > 0),
            type        TEXT NOT NULL CHECK(type IN ('income','expense')),
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            notes       TEXT,
            created_by  TEXT NOT NULL,
            deleted_at  TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_records_type     ON financial_records(type);
        CREATE INDEX IF NOT EXISTS idx_records_category ON financial_records(category);
        CREATE INDEX IF NOT EXISTS idx_records_date     ON financial_records(date);
        CREATE INDEX IF NOT EXISTS idx_records_deleted  ON financial_records(deleted_at);
        CREATE INDEX IF NOT EXISTS idx_users_email      ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_status     ON users(status);
    """)
    conn.commit()
    conn.close()
