"""Student login / registration and teacher login"""

from flask import Blueprint, redirect, render_template, request, session

import config
import models

bp = Blueprint('auth', __name__)


@bp.route('/')
def login_page():
    if session.get('sid'):
        return redirect('/home')
    return render_template('login.html', error=None)


@bp.route('/login')
def login_redirect():
    return redirect('/')


@bp.route('/login', methods=['POST'])
def login():
    student = models.find_student(request.form.get('sid', ''))
    if not student:
        return render_template('login.html', error='Invalid Student ID')
    session['sid'] = student['sid']
    return redirect('/home')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@bp.route('/register')
def register_page():
    return render_template('register.html', error=None, success=None)


@bp.route('/register', methods=['POST'])
def register():
    sid = request.form.get('sid', '').strip()
    sname = request.form.get('sname', '').strip()
    email = request.form.get('email', '').strip()
    if not sid or not sname:
        return render_template('register.html',
                               error='SID and Name are required.', success=None)
    if models.find_student(sid):
        return render_template('register.html',
                               error='Student ID already registered.', success=None)
    models.add_student(sid, sname, email or None)
    return render_template('register.html', error=None,
                           success='Registered successfully! You can now sign in.')


@bp.route('/teacher/login')
def teacher_login_page():
    if session.get('teacher'):
        return redirect('/teacher')
    return render_template('teacher-login.html', error=None)


@bp.route('/teacher/login', methods=['POST'])
def teacher_login():
    if request.form.get('password') == config.ADMIN_PASSWORD:
        session['teacher'] = True
        return redirect('/teacher')
    return render_template('teacher-login.html', error='Incorrect password.')


@bp.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher', None)
    return redirect('/teacher/login')
