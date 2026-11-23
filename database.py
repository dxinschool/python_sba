"""Creates the SQLite database file, the tables, and the sample data.

SQLite is built into Python, so there is nothing to install and no server
to run. The entire database is the single file `election.db`.
"""

import os
import sqlite3

from flask import g

import config

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.DATABASE_FILE)

# The tables. This is the picture from project.md turned into SQL:
#   Student --Vote--> Candidate --Has--> Members
SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    sid     TEXT PRIMARY KEY,               -- Student ID (key)
    sname   TEXT NOT NULL,                  -- Student name
    email   TEXT,                           -- Email
    vstatus INTEGER NOT NULL DEFAULT 0      -- Vote status (0 = not voted, 1 = voted)
);

CREATE TABLE IF NOT EXISTS candidates (
    cid         INTEGER PRIMARY KEY AUTOINCREMENT,  -- Candidate ID (key)
    cname       TEXT NOT NULL,                      -- Candidate name
    votes       INTEGER NOT NULL DEFAULT 0,         -- Votes (cached first-choice count)
    description TEXT,                               -- Description
    slug        TEXT NOT NULL UNIQUE,               -- extra: friendly URL for the profile page
    sid         TEXT REFERENCES students(sid)        -- extra: stops candidates from voting
);

CREATE TABLE IF NOT EXISTS votes (
    voter_sid     TEXT NOT NULL REFERENCES students(sid),
    candidate_cid INTEGER NOT NULL REFERENCES candidates(cid),
    preference    INTEGER NOT NULL CHECK (preference >= 1),
    PRIMARY KEY (voter_sid, candidate_cid),
    UNIQUE (voter_sid, preference)
);

CREATE TABLE IF NOT EXISTS members (
    sid      TEXT NOT NULL REFERENCES students(sid),        -- Student ID (part of key)
    cid      INTEGER NOT NULL REFERENCES candidates(cid),   -- Candidate ID (part of key)
    mname    TEXT NOT NULL,                                  -- Member name
    position TEXT NOT NULL,                                  -- position / role
    PRIMARY KEY (sid, cid)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Sample students. The last six are campaign members, added so that every
# row in `members` can point at a real student (foreign key).
STUDENTS = [
    ('SBA-2401', 'Juan Dela Cruz',   'juan@example.com'),
    ('SBA-2402', 'Maria Reyes',      'maria@example.com'),
    ('SBA-2403', 'Carlos Santos',    'carlos@example.com'),
    ('SBA-2404', 'Ana Gonzales',     'ana@example.com'),
    ('SBA-2405', 'Pedro Lim',        'pedro@example.com'),
    ('SBA-2406', 'Maria Santos',     'maria.santos@example.com'),
    ('SBA-2407', 'Jose Garcia',      'jose.garcia@example.com'),
    ('SBA-2408', 'Elena Rodriguez',  'elena.rodriguez@example.com'),
    ('SBA-2409', 'Anna Reyes',       'anna.reyes@example.com'),
    ('SBA-2410', 'Ben Torres',       'ben.torres@example.com'),
    ('SBA-2411', 'Carla Gomez',      'carla.gomez@example.com'),
    ('SBA-2412', 'Ding Cruz',        'ding.cruz@example.com'),
    ('SBA-2413', 'Franco Lopez',     'franco.lopez@example.com'),
    ('SBA-2414', 'Grace Tan',        'grace.tan@example.com'),
]

# slug, name, description, linked student id
CANDIDATES = [
    ('maria-santos', 'Maria Santos',
     'Improve campus facilities, add more student lounges, and strengthen the SBA funding for club activities.',
     'SBA-2406'),
    ('jose-garcia', 'Jose Garcia',
     'Focus on academic support programs, tutoring centers, and mental health awareness campaigns.',
     'SBA-2407'),
    ('elena-rodriguez', 'Elena Rodriguez',
     'Promote environmental sustainability, tree planting initiatives, and eco-friendly school policies.',
     'SBA-2408'),
]

# candidate number (cid), member student id, name, role
MEMBERS = [
    (1, 'SBA-2409', 'Anna Reyes',   'Campaign Manager'),
    (1, 'SBA-2410', 'Ben Torres',   'Treasurer'),
    (2, 'SBA-2411', 'Carla Gomez',  'Campaign Manager'),
    (2, 'SBA-2412', 'Ding Cruz',    'Logistics Head'),
    (3, 'SBA-2413', 'Franco Lopez', 'Campaign Manager'),
    (3, 'SBA-2414', 'Grace Tan',    'Secretary'),
]

SETTINGS = [
    ('voting_enabled', 'true'),
    ('election_deadline', config.DEFAULT_DEADLINE),
]


def init_db():
    """Run once at startup. Safe to run again - nothing is overwritten."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.executescript(SCHEMA)
        conn.executemany(
            'INSERT OR IGNORE INTO students (sid, sname, email) VALUES (?, ?, ?)',
            STUDENTS,
        )
        conn.executemany(
            'INSERT OR IGNORE INTO candidates (slug, cname, description, sid) VALUES (?, ?, ?, ?)',
            CANDIDATES,
        )
        conn.executemany(
            'INSERT OR IGNORE INTO members (cid, sid, mname, position) VALUES (?, ?, ?, ?)',
            MEMBERS,
        )
        conn.executemany(
            'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
            SETTINGS,
        )
        conn.commit()
    finally:
        conn.close()


def get_db():
    """One database connection per web request, stored on Flask's `g` object."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    """Close the connection when the request is finished."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
