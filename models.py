import re
from datetime import datetime

import config
import database
import irv


def one(sql, params=()):
    row = database.get_db().execute(sql, params).fetchone()
    return row


def all_rows(sql, params=()):
    return database.get_db().execute(sql, params).fetchall()


def execute(sql, params=()):
    return database.get_db().execute(sql, params)


# ---------------------------------------------------------------- students

def find_student(sid):
    return one('SELECT * FROM students WHERE sid = ?', (sid,))


def add_student(sid, sname, email):
    execute('INSERT INTO students (sid, sname, email) VALUES (?, ?, ?)',
            (sid, sname, email))


def all_students():
    return all_rows('SELECT * FROM students ORDER BY sid')


def total_voters():
    return one('SELECT COUNT(*) AS count FROM students')['count']


def is_candidate(sid):
    return one('SELECT COUNT(*) AS count FROM candidates WHERE sid = ?', (sid,))['count'] > 0


def has_voted(sid):
    student = find_student(sid)
    return bool(student and student['vstatus'])


def total_votes_cast():
    return one('SELECT COUNT(*) AS count FROM students WHERE vstatus = 1')['count']


# --------------------------------------------------------------- candidates

def all_candidates():
    return all_rows('SELECT * FROM candidates ORDER BY cid')


def candidate_by_slug(slug):
    return one('SELECT * FROM candidates WHERE slug = ?', (slug,))


def candidate(cid):
    return one('SELECT * FROM candidates WHERE cid = ?', (cid,))


def candidate_by_sid(sid):
    return one('SELECT * FROM candidates WHERE sid = ?', (sid,))


def make_slug(name):
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')


def add_candidate(cname, sid=None):
    slug = make_slug(cname)
    cur = execute('INSERT INTO candidates (cname, slug, sid) VALUES (?, ?, ?)',
                  (cname, slug, sid or None))
    return cur.lastrowid


def update_candidate(cid, cname, description, sid=None):
    execute('UPDATE candidates SET cname = ?, description = ?, sid = ? WHERE cid = ?',
            (cname, description, sid or None, cid))


def update_description(cid, description):
    execute('UPDATE candidates SET description = ? WHERE cid = ?', (description, cid))


def delete_candidate(cid):
    db = database.get_db()
    with db:
        db.execute('DELETE FROM votes WHERE candidate_cid = ?', (cid,))
        db.execute('DELETE FROM members WHERE cid = ?', (cid,))
        db.execute('DELETE FROM candidates WHERE cid = ?', (cid,))
        refresh_counts(db)


def refresh_counts(db=None):
    """Keep the `votes` column on each candidate up to date."""
    db = db or database.get_db()
    db.execute("""UPDATE candidates SET votes = (
                      SELECT COUNT(*) FROM votes v
                      WHERE v.candidate_cid = candidates.cid AND v.preference = 1
                  )""")


# ------------------------------------------------------------------ members

def members_of(cid):
    return all_rows('SELECT * FROM members WHERE cid = ? ORDER BY rowid', (cid,))


def add_member(sid, cid, mname, position):
    execute('INSERT INTO members (sid, cid, mname, position) VALUES (?, ?, ?, ?)',
            (sid, cid, mname, position or ''))


def delete_member(sid, cid):
    execute('DELETE FROM members WHERE sid = ? AND cid = ?', (sid, cid))


# ------------------------------------------------------------------- voting

def cast_vote(sid, preferences):
    """Replace this student's ballot. All statements commit together or not at all."""
    db = database.get_db()
    with db:
        db.execute('DELETE FROM votes WHERE voter_sid = ?', (sid,))
        for rank, cid in enumerate(preferences, start=1):
            db.execute('INSERT INTO votes (voter_sid, candidate_cid, preference) '
                       'VALUES (?, ?, ?)', (sid, cid, rank))
        db.execute('UPDATE students SET vstatus = 1 WHERE sid = ?', (sid,))
        refresh_counts(db)


def blank_votes():
    return one("""SELECT COUNT(*) AS count FROM students s
                  WHERE s.vstatus = 1
                    AND NOT EXISTS (SELECT 1 FROM votes v WHERE v.voter_sid = s.sid)""")['count']


def reset_election():
    db = database.get_db()
    with db:
        db.execute('DELETE FROM votes')
        db.execute('UPDATE students SET vstatus = 0')
        refresh_counts(db)


# ----------------------------------------------------------------- settings

def setting(key, default=None):
    row = one('SELECT value FROM settings WHERE key = ?', (key,))
    return row['value'] if row else default


def set_setting(key, value):
    execute("""INSERT INTO settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""", (key, value))


def election_over():
    deadline = setting('election_deadline', config.DEFAULT_DEADLINE)
    return datetime.now() >= datetime.fromisoformat(deadline)


# ------------------------------------------------------------------ results

def results():
    rows = all_rows('SELECT voter_sid, candidate_cid, preference '
                    'FROM votes ORDER BY voter_sid, preference')
    return irv.tally(all_candidates(), rows, total_voters(), blank_votes())
