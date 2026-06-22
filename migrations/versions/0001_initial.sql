-- 0001_initial.sql: create baseline tables (idempotent)

CREATE TABLE IF NOT EXISTS migrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  difficulty INTEGER NOT NULL,
  enjoyment INTEGER NOT NULL,
  workload INTEGER NOT NULL,
  review TEXT NOT NULL,
  created_at TEXT NOT NULL,
  flagged INTEGER DEFAULT 0
);

PRAGMA user_version = 1;
