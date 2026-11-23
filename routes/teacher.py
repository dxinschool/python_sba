"""Everything behind the teacher password."""

from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for

import config
import models
from routes.helpers import require_teacher

bp = Blueprint('teacher', __name__)


@bp.route('/teacher')
@require_teacher
def dashboard():
    raw_candidates = models.all_candidates()
    candidates = [{'CID': c['cid'], 'CNAME': c['cname'], 'DESC': c['description']}
                  for c in raw_candidates]
    raw_deadline = models.setting('election_deadline', config.DEFAULT_DEADLINE)
    d = datetime.fromisoformat(raw_deadline)
    return render_template(
        'teacher.html',
        totalStudents=models.total_voters(),
        totalVoted=models.total_votes_cast(),
        blankVotes=models.blank_votes(),
        candidates=candidates,
        votingEnabled=models.setting('voting_enabled', 'true') == 'true',
        deadlineInput=d.strftime('%Y-%m-%dT%H:%M'),
        deadlineDisplay=d.strftime('%Y-%m-%d %H:%M:%S'),
        success=request.args.get('success'),
        error=request.args.get('error'),
    )


@bp.route('/teacher/settings', methods=['POST'])
@require_teacher
def settings():
    deadline = request.form.get('deadline')
    if deadline:
        models.set_setting('election_deadline', deadline + ':59')
        return redirect(url_for('teacher.dashboard', success='Deadline updated'))
    return redirect(url_for('teacher.dashboard', success='No change'))


@bp.route('/teacher/reset', methods=['POST'])
@require_teacher
def reset():
    models.reset_election()
    return redirect(url_for('teacher.dashboard', success='Election reset successfully'))


@bp.route('/teacher/toggle-voting', methods=['POST'])
@require_teacher
def toggle_voting():
    current = models.setting('voting_enabled', 'true') == 'true'
    models.set_setting('voting_enabled', 'false' if current else 'true')
    message = 'Voting disabled' if current else 'Voting enabled'
    return redirect(url_for('teacher.dashboard', success=message))


@bp.route('/teacher/candidate/add', methods=['POST'])
@require_teacher
def add_candidate():
    cname = request.form.get('cname', '').strip()
    sid = request.form.get('sid', '').strip()
    if not cname:
        return redirect(url_for('teacher.dashboard', error='Name is required'))
    if sid:
        if not models.find_student(sid):
            return redirect(url_for('teacher.dashboard', error='Student ID not found'))
        existing = models.candidate_by_sid(sid)
        if existing:
            return redirect(url_for('teacher.dashboard',
                                    error='SID already linked to ' + existing['cname']))
    models.add_candidate(cname, sid or None)
    return redirect(url_for('teacher.dashboard', success='Candidate added'))


@bp.route('/teacher/candidate/delete', methods=['POST'])
@require_teacher
def delete_candidate():
    cid = request.form.get('cid', type=int)
    if not cid:
        return redirect(url_for('teacher.dashboard', error='Invalid candidate'))
    models.delete_candidate(cid)
    return redirect(url_for('teacher.dashboard', success='Candidate deleted'))


@bp.route('/teacher/candidate/member/add', methods=['POST'])
@require_teacher
def add_member():
    cid = request.form.get('cid', type=int)
    sid = request.form.get('sid', '').strip()
    mname = request.form.get('mname', '').strip()
    role = request.form.get('role', '').strip()
    if not cid or not mname or not sid:
        return redirect(url_for('teacher.edit_candidate', cid=cid or 0,
                                error='Member name and Student ID are required'))
    if not models.find_student(sid):
        return redirect(url_for('teacher.edit_candidate', cid=cid,
                                error='Student ID not found'))
    models.add_member(sid, cid, mname, role)
    return redirect(url_for('teacher.edit_candidate', cid=cid, success='Member added'))


@bp.route('/teacher/candidate/member/delete', methods=['POST'])
@require_teacher
def delete_member():
    sid = request.form.get('sid', '').strip()
    cid = request.form.get('cid', type=int)
    if not sid or not cid:
        return redirect(url_for('teacher.dashboard', error='Invalid member'))
    models.delete_member(sid, cid)
    return redirect(url_for('teacher.edit_candidate', cid=cid, success='Member removed'))


@bp.route('/teacher/candidate/edit/<int:cid>')
@require_teacher
def edit_candidate(cid):
    raw = models.candidate(cid)
    if not raw:
        return redirect(url_for('teacher.dashboard', error='Candidate not found'))
    candidate = {'CID': raw['cid'], 'CNAME': raw['cname'],
                 'DESC': raw['description'], 'SID': raw['sid']}
    return render_template(
        'teacher-candidate-edit.html',
        candidate=candidate,
        success=request.args.get('success'),
        error=request.args.get('error'),
    )


@bp.route('/teacher/candidate/edit/<int:cid>', methods=['POST'])
@require_teacher
def update_candidate(cid):
    cname = request.form.get('cname', '').strip()
    sid = request.form.get('sid', '').strip()
    if not cname:
        return redirect(url_for('teacher.edit_candidate', cid=cid, error='Name is required'))
    current = models.candidate(cid)
    if not current:
        return redirect(url_for('teacher.dashboard', error='Candidate not found'))
    if sid:
        if not models.find_student(sid):
            return redirect(url_for('teacher.edit_candidate', cid=cid,
                                    error='Student ID not found'))
        existing = models.candidate_by_sid(sid)
        if existing and existing['cid'] != cid:
            return redirect(url_for('teacher.edit_candidate', cid=cid,
                                    error='SID already linked to ' + existing['cname']))
    # The description is managed by the candidate, so keep the current one.
    models.update_candidate(cid, cname, current['description'], sid or None)
    return redirect(url_for('teacher.dashboard', success='Candidate updated'))
