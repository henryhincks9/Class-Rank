import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
DB_FILE = DATA_DIR / 'app.db'
MIGRATIONS_DIR = ROOT / 'migrations' / 'versions'


def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_migrations_table(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS migrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        applied_at TEXT NOT NULL
    )''')
    conn.commit()


def applied_migrations(conn):
    rows = conn.execute('SELECT name FROM migrations').fetchall()
    return {r['name'] for r in rows}


def apply_migration(conn, name, sql_text):
    print(f'Applying migration: {name}')
    try:
        conn.executescript(sql_text)
    except sqlite3.OperationalError as error:
        message = str(error).lower()
        if 'duplicate column name' in message or 'already exists' in message:
            print(f'  Migration may already exist: {error}')
        else:
            raise
    conn.execute('INSERT INTO migrations (name, applied_at) VALUES (?, ?)', (name, datetime.now(timezone.utc).isoformat()))
    conn.commit()


def run_migrations():
    if not MIGRATIONS_DIR.exists():
        print('No migrations directory found; nothing to do.')
        return
    conn = get_conn()
    ensure_migrations_table(conn)
    applied = applied_migrations(conn)
    files = sorted([p for p in MIGRATIONS_DIR.iterdir() if p.suffix == '.sql'])
    for f in files:
        name = f.name
        if name in applied:
            print(f'Skipping already applied: {name}')
            continue
        sql = f.read_text(encoding='utf-8')
        apply_migration(conn, name, sql)
    conn.close()


if __name__ == '__main__':
    run_migrations()
