"""Two small guards: 'are you a student?' and 'are you the teacher?'"""

from functools import wraps

from flask import redirect, session


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('sid'):
            return redirect('/')
        return view(*args, **kwargs)
    return wrapped


def require_teacher(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('teacher'):
            return redirect('/teacher/login')
        return view(*args, **kwargs)
    return wrapped
