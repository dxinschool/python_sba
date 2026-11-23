# SBA Election — Python version

The same election system as the Node.js build, rewritten in beginner-friendly
Python. Same pages, same features, same look — but the database is now a single
file called `election.db` and there is no Supabase/PostgreSQL to set up.

## Run it

```bash
pip install flask        # the only thing you need to install
python app.py
```

Open **http://127.0.0.1:5000** in your browser. That's it.

- Student logins are already in the database: `SBA-2401` … `SBA-2414`.
- Candidates (cannot vote): `SBA-2406`, `SBA-2407`, `SBA-2408`.
- Teacher login: `/teacher/login`, password `teacher123`.

`election.db` is created automatically on the first run with sample data.
Delete the file to start over from scratch.

## No admin rights on the school computer?

`pip install --user flask` installs Flask into your own user folder — no admin
password needed. If Python itself is missing, put a portable Python (e.g.
WinPython) on a USB stick together with this folder and run from there.

If the Wi-Fi is unreliable, pre-download the installer on your own laptop:

```bash
pip download flask -d wheels
pip install --no-index --find-links=wheels flask
```

## What is in each file

| File | Job |
|------|-----|
| `app.py` | Starts the server and wires everything together |
| `config.py` | Title, secret key, password, deadline — the settings you might change |
| `database.py` | Creates the tables and sample data on first run |
| `models.py` | All SQL queries, grouped by entity |
| `irv.py` | The ranked-choice vote counting — pure Python, no web stuff |
| `routes/` | One file per part of the site: login, voting, teacher, candidate panel |
| `templates/` | The same 10 pages as before, with Jinja instead of EJS tags |

## The database (matches the hand-drawn ER diagram)

```
students (sid, sname, email, vstatus)   -- Vote status is a real column
    |                                                    |
    | Vote (M : 1)                                       |
    v                                                    v
candidates (cid, cname, votes, description, slug, sid) <-- votes table
    |
    | Has (1 : N)
    v
members (sid, cid, mname, position)   -- composite key: Student ID + Candidate ID
```

`votes` stores the ranking (`preference`) behind the scenes so the ranked
ballot and IRV rounds still work. `slug`, `candidates.sid` and `settings` are
small extras the old build also needed.
