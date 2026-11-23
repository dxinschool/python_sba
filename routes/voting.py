"""The pages a normal student uses: dashboard, candidates, vote, results."""

from flask import Blueprint, redirect, render_template, request, session

import models
from routes.helpers import require_auth

bp = Blueprint('voting', __name__)


@bp.route('/home')
@require_auth
def home():
    raw = models.find_student(session['sid'])
    student = {'SID': raw['sid'], 'SNAME': raw['sname'], 'EMAIL': raw['email']}
    return render_template(
        'home.html',
        student=student,
        candidates=models.all_candidates(),
        totalVoters=models.total_voters(),
        voted=models.has_voted(session['sid']),
        isCandidate=models.is_candidate(session['sid']),
        votingEnabled=models.setting('voting_enabled', 'true') == 'true',
        success=request.args.get('voted') == '1',
    )


@bp.route('/candidates')
@require_auth
def candidates():
    raw = models.all_candidates()
    candidates_list = [{'CID': c['cid'], 'CNAME': c['cname'],
                        'SLUG': c['slug'], 'DESC': c['description']} for c in raw]
    return render_template(
        'candidates.html',
        candidates=candidates_list,
        viewOnly=request.args.get('view') == '1',
        votingEnabled=models.setting('voting_enabled', 'true') == 'true',
    )


@bp.route('/candidate/<slug>')
@require_auth
def candidate_profile(slug):
    raw = models.candidate_by_slug(slug)
    if not raw:
        return 'Association not found', 404
    candidate = {'CID': raw['cid'], 'CNAME': raw['cname'],
                 'SLUG': raw['slug'], 'DESC': raw['description']}
    members = [{'MNAME': m['mname'], 'POSITION': m['position']}
               for m in models.members_of(raw['cid'])]
    return render_template('candidate.html', candidate=candidate, members=members,
                           view=request.args.get('view') == '1')


@bp.route('/vote', methods=['POST'])
@require_auth
def vote():
    if models.election_over():
        return 'Voting has ended.', 403
    if models.is_candidate(session['sid']):
        return 'Candidates cannot vote.', 403
    if models.setting('voting_enabled', 'true') != 'true':
        return 'Voting is currently disabled by the administrator.', 403

    candidates_list = models.all_candidates()
    preferences = []
    for i in range(1, len(candidates_list) + 1):
        value = request.form.get('pref{}'.format(i))
        if value:
            preferences.append(int(value))
        else:
            break

    models.cast_vote(session['sid'], preferences)
    return redirect('/home?voted=1')


@bp.route('/results')
def results():
    data = models.results()
    candidates_list = [{'CID': c['cid'], 'CNAME': c['cname']}
                       for c in models.all_candidates()]
    votes_cast = 0
    if data['rounds']:
        votes_cast = sum(v['count'] for v in data['rounds'][0]['votes'])
    return render_template('results.html', winner=data['winner'],
                           electionOver=models.election_over(),
                           totalVoters=data['total_voters'],
                           blankVotes=data['blank_votes'],
                           votes_cast=votes_cast,
                           rounds=data['rounds'],
                           candidates=candidates_list)
