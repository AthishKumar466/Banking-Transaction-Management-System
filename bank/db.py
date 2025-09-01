import sqlite3
from pathlib import Path

SCHEMA = '''
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    balance REAL NOT NULL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    counterparty INTEGER,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
'''

def get_conn(db_path='bank.db'):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db(db_path='bank.db'):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn(db_path)
    with conn:
        conn.executescript(SCHEMA)
    conn.close()
