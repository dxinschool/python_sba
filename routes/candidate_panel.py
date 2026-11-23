"""The self-service page for students who are running in the election."""

from flask import Blueprint, redirect, render_template, request, session, url_for

import models
from routes.helpers import require_auth

bp = Blueprint('candidate_panel', __name__)


def my_candidate():
    """Return the logged-in student's candidate row, or None."""
    return models.candidate_by_sid(session['sid'])


@bp.route('/candidate-panel')
@require_auth
def panel():
    if not models.is_candidate(session['sid']):
        return 'You are not a candidate.', 403
    raw = my_candidate()
    if not raw:
        return 'Candidate not found', 404
    candidate = {'CID': raw['cid'], 'CNAME': raw['cname'],
                 'SLUG': raw['slug'], 'DESC': raw['description'], 'SID': raw['sid']}
    members = [{'SID': m['sid'], 'MNAME': m['mname'], 'POSITION': m['position']}
               for m in models.members_of(raw['cid'])]
    return render_template(
        'candidate-panel.html',
        candidate=candidate,
        members=members,
        students=models.all_students(),
        success=request.args.get('success'),
        error=request.args.get('error'),
    )


@bp.route('/candidate-panel/description', methods=['POST'])
@require_auth
def update_description():
    candidate = my_candidate()
    if not candidate:
        return 'Not a candidate', 403
    models.update_description(candidate['cid'], request.form.get('description', '').strip())
    return redirect(url_for('candidate_panel.panel', success='Description updated'))


@bp.route('/candidate-panel/member/add', methods=['POST'])
@require_auth
def add_member():
    candidate = my_candidate()
    if not candidate:
        return 'Not a candidate', 403
    sid = request.form.get('sid', '').strip()
    mname = request.form.get('mname', '').strip()
    role = request.form.get('role', '').strip()
    if not mname or not sid:
        return redirect(url_for('candidate_panel.panel',
                                error='Member name and Student ID are required'))
    if not models.find_student(sid):
        return redirect(url_for('candidate_panel.panel', error='Student ID not found'))
    models.add_member(sid, candidate['cid'], mname, role)
    return redirect(url_for('candidate_panel.panel', success='Member added'))


@bp.route('/candidate-panel/member/delete', methods=['POST'])
@require_auth
def delete_member():
    candidate = my_candidate()
    if not candidate:
        return 'Not a candidate', 403
    sid = request.form.get('sid', '').strip()
    if not sid:
        return redirect(url_for('candidate_panel.panel', error='Invalid member'))
    # Only allow removing someone who really belongs to this candidate.
    if not any(m['sid'] == sid for m in models.members_of(candidate['cid'])):
        return redirect(url_for('candidate_panel.panel', error='Member not found'))
    models.delete_member(sid, candidate['cid'])
    return redirect(url_for('candidate_panel.panel', success='Member removed'))
