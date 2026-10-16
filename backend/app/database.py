import os, sqlite3
from contextlib import contextmanager
DB_PATH = os.getenv('DATABASE_PATH', './krishimitra.db')
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute('CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL DEFAULT "", created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
        columns={row[1] for row in db.execute('PRAGMA table_info(conversations)')}
        if 'owner_id' not in columns:
            db.execute('ALTER TABLE conversations ADD COLUMN owner_id TEXT NOT NULL DEFAULT ""')
        db.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(conversation_id) REFERENCES conversations(id))')
@contextmanager
def connect():
    db=sqlite3.connect(DB_PATH); db.row_factory=sqlite3.Row
    try:
        yield db
        db.commit()
    finally: db.close()
