"""Instant-runoff voting (ranked-choice) - the vote-counting brain.

This file is pure Python: it knows nothing about Flask or the database.
You can show just this file to explain how a winner is chosen.

Rules:
  1. Count each ballot's highest-ranked candidate who is still in the race.
  2. If someone has more than half the active votes, they win.
  3. If everyone is tied, stop (no winner).
  4. Otherwise eliminate every candidate with the fewest votes and go to 1 again.
"""


def tally(candidates, vote_rows, total_voters, blank_votes):
    # Group the flat vote rows into one ordered list of choices per voter.
    ballots = {}
    for row in vote_rows:
        ballots.setdefault(row['voter_sid'], []).append(
            {'cid': row['candidate_cid'], 'pref': row['preference']}
        )
    all_ballots = list(ballots.values())

    if not all_ballots:
        return {'rounds': [], 'winner': None,
                'total_voters': total_voters, 'blank_votes': blank_votes}

    def name_of(cid):
        for c in candidates:
            if c['cid'] == cid:
                return c['cname']
        return None

    rounds = []
    eliminated = []
    remaining = [c['cid'] for c in candidates]
    round_num = 1

    while len(remaining) > 1:
        counts = {cid: 0 for cid in remaining}

        # Each ballot goes to its first choice that has not been eliminated.
        for ballot in all_ballots:
            for vote in ballot:
                if vote['cid'] not in eliminated:
                    counts[vote['cid']] += 1
                    break

        total_active = sum(counts.values())
        sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        vote_data = [{'name': name_of(cid), 'count': counts[cid]} for cid in remaining]

        # More than half of the active votes -> winner.
        if sorted_counts[0][1] > total_active / 2:
            rounds.append({'label': 'Round {}'.format(round_num), 'votes': vote_data})
            break

        # Everybody tied -> no winner.
        if len(set(counts.values())) == 1:
            rounds.append({'label': 'Round {}'.format(round_num), 'votes': vote_data})
            break

        # Eliminate all candidates who have the fewest votes.
        lowest = min(counts.values())
        to_eliminate = [cid for cid in remaining if counts[cid] == lowest]
        eliminated_text = ', '.join(filter(None, (name_of(cid) for cid in to_eliminate)))
        rounds.append({'label': 'Round {}'.format(round_num),
                       'votes': vote_data, 'eliminated': eliminated_text})

        eliminated += to_eliminate
        remaining = [cid for cid in remaining if cid not in eliminated]
        round_num += 1

    # Work out the winner from the final round.
    winner = None
    if remaining:
        final_counts = {cid: 0 for cid in remaining}
        for ballot in all_ballots:
            for vote in ballot:
                if vote['cid'] not in eliminated:
                    final_counts[vote['cid']] += 1
                    break

        ordered = sorted(final_counts.items(), key=lambda item: item[1], reverse=True)
        if ordered:
            if len(ordered) == 1 or ordered[0][1] > ordered[1][1]:
                winner = name_of(ordered[0][0])

    return {'rounds': rounds, 'winner': winner,
            'total_voters': total_voters, 'blank_votes': blank_votes}
