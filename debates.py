# ============================================================
# debates.py
# Covers: debate create/view/list, voting, comments
# ============================================================
# Scoring system:
#   +20  reputation for creating a debate
#   +5   reputation for casting a vote
#   +10  reputation for posting a comment or reply
#   +2   reputation awarded to comment author when their comment is liked
#   Conformity score: % of a user's votes that matched the winning side
#                     (recalculated on debate close, draws excluded)
# ============================================================

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
from models import db, Debate, Vote, Comment, CommentLike

debates_bp = Blueprint('debates', __name__)


def close_debate(debate):
    """
    Declares the winner of an expired debate.
    Updates debates_won / debates_lost for all voters.
    Recalculates conformity_score for each voter.
    Only runs once — skipped if winner is already set.
    """
    if debate.winner is not None:
        return  # Already closed

    # --- Determine winner ---
    if debate.agree_votes > debate.disagree_votes:
        debate.winner = 'agree'
    elif debate.disagree_votes > debate.agree_votes:
        debate.winner = 'disagree'
    else:
        debate.winner = 'draw'

    debate.is_closed = True

    # --- Update won/lost record for all voters (not for draws) ---
    if debate.winner != 'draw':
        for vote in debate.votes:
            if vote.vote_type == debate.winner:
                vote.user.debates_won += 1
            else:
                vote.user.debates_lost += 1

        # --- Recalculate conformity score for each voter ---
        # Conformity = how often this user has voted with the majority
        # across all closed non-draw debates they participated in.
        # SQLAlchemy autoflushes debate.winner before these queries run,
        # so the current debate's result is included in the calculation.
        for vote in debate.votes:
            user = vote.user

            # Total closed non-draw debates this user voted in
            total = (
                db.session.query(Vote)
                .join(Debate, Vote.debate_id == Debate.id)
                .filter(Vote.user_id == user.id)
                .filter(Debate.winner.isnot(None))
                .filter(Debate.winner != 'draw')
                .count()
            )

            # How many times they voted with the winning side
            correct = (
                db.session.query(Vote)
                .join(Debate, Vote.debate_id == Debate.id)
                .filter(Vote.user_id == user.id)
                .filter(Debate.winner.isnot(None))
                .filter(Debate.winner != 'draw')
                .filter(Vote.vote_type == Debate.winner)
                .count()
            )

            if total > 0:
                user.conformity_score = round(correct / total, 4)

    db.session.commit()


# ============================================================
# DEBATE ROUTES
# ============================================================

@debates_bp.route('/debates/create', methods=['GET', 'POST'])
@login_required
def create_debate():
    """
    GET  — render the create debate form.
    POST — validate input, save debate, award +20 reputation, redirect.
    """
    if request.method == 'GET':
        return render_template('create_debate.html')

    title        = request.form.get('title', '').strip()
    description  = request.form.get('description', '').strip()
    category     = request.form.get('category', '').strip()
    is_anonymous = request.form.get('is_anonymous') == 'on'
    is_private   = request.form.get('is_private') == 'on'

    try:
        duration_days = int(request.form.get('duration_days', 1))
    except ValueError:
        duration_days = 1

    errors = []
    if not title:
        errors.append('Title is required.')
    if not description:
        errors.append('Description is required.')
    if not category:
        errors.append('Category is required.')
    if duration_days < 1 or duration_days > 14:
        errors.append('Duration must be between 1 and 14 days.')

    if errors:
        return render_template('create_debate.html', errors=errors)

    expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

    debate = Debate(
        title        = title,
        description  = description,
        category     = category,
        expires_at   = expires_at,
        is_anonymous = is_anonymous,
        is_private   = is_private,
        user_id      = current_user.id,
    )

    # Award participation points for creating a debate
    current_user.reputation_score += 20

    db.session.add(debate)
    db.session.commit()

    return redirect(url_for('debates.view_debate', debate_id=debate.id))


@debates_bp.route('/debates/<int:debate_id>')
def view_debate(debate_id):
    """
    Displays a single debate page.
    Vote distribution is hidden while the debate is active.
    Full results shown after expiry, which also triggers close_debate().
    """
    debate = db.get_or_404(Debate, debate_id)

    if debate.is_active:
        vote_data = {
            'total':    debate.total_votes,
            'revealed': False,
        }
    else:
        close_debate(debate)
        total = debate.total_votes
        if total == 0:
            vote_data = {
                'revealed':     True,
                'total':        0,
                'agree_pct':    0,
                'disagree_pct': 0,
                'winner':       debate.winner,
            }
        else:
            vote_data = {
                'revealed':     True,
                'total':        total,
                'agree':        debate.agree_votes,
                'disagree':     debate.disagree_votes,
                'agree_pct':    round((debate.agree_votes / total) * 100, 1),
                'disagree_pct': round((debate.disagree_votes / total) * 100, 1),
                'winner':       debate.winner,
            }

    top_level_comments = Comment.query.filter_by(
        debate_id         = debate_id,
        parent_comment_id = None
    ).order_by(Comment.created_at.asc()).all()

    user_vote = None
    if current_user.is_authenticated:
        user_vote = Vote.query.filter_by(
            user_id   = current_user.id,
            debate_id = debate_id
        ).first()

    return render_template(
        'debate.html',
        debate    = debate,
        vote_data = vote_data,
        comments  = top_level_comments,
        user_vote = user_vote,
    )


@debates_bp.route('/debates')
def debate_list():
    """Returns all debates for the dashboard feed, newest first."""
    debates = Debate.query.order_by(Debate.created_at.desc()).all()
    return render_template('dashboard.html', debates=debates)


# ============================================================
# VOTING
# ============================================================

@debates_bp.route('/debates/<int:debate_id>/vote', methods=['POST'])
@login_required
def cast_vote(debate_id):
    """
    Records an Agree or Disagree vote and awards +5 reputation.
    Rules: debate must be active, one vote per user per debate.
    Returns JSON for AJAX calls.
    """
    debate = db.get_or_404(Debate, debate_id)

    if not debate.is_active:
        return jsonify({'error': 'This debate has closed — voting is no longer allowed.'}), 400

    vote_type = request.form.get('vote_type', '').lower()
    if vote_type not in ('agree', 'disagree'):
        return jsonify({'error': 'Invalid vote type. Must be agree or disagree.'}), 400

    existing = Vote.query.filter_by(
        user_id   = current_user.id,
        debate_id = debate_id
    ).first()

    if existing:
        return jsonify({'error': 'You have already voted on this debate.'}), 400

    vote = Vote(
        user_id   = current_user.id,
        debate_id = debate_id,
        vote_type = vote_type,
    )

    if vote_type == 'agree':
        debate.agree_votes += 1
    else:
        debate.disagree_votes += 1

    # Award participation points for voting
    current_user.reputation_score += 5

    try:
        db.session.add(vote)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'You have already voted on this debate.'}), 400

    return jsonify({
        'success': True,
        'total':   debate.total_votes,
    })


# ============================================================
# COMMENTS
# ============================================================

@debates_bp.route('/debates/<int:debate_id>/comments', methods=['POST'])
@login_required
def post_comment(debate_id):
    """
    Posts a top-level comment. Awards +10 reputation to commenter.
    Returns JSON.
    """
    debate = db.get_or_404(Debate, debate_id)

    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Comment cannot be empty.'}), 400

    comment = Comment(
        user_id           = current_user.id,
        debate_id         = debate_id,
        content           = content,
        parent_comment_id = None,
    )

    # Award participation points for commenting
    current_user.reputation_score += 10

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'success':    True,
        'comment_id': comment.id,
        'username':   current_user.username,
        'content':    comment.content,
        'created_at': comment.created_at.strftime('%d %b %Y, %H:%M'),
    })


@debates_bp.route('/comments/<int:comment_id>/reply', methods=['POST'])
@login_required
def post_reply(comment_id):
    """
    Posts a reply to an existing comment. Awards +10 reputation to replier.
    Returns JSON.
    """
    parent = db.get_or_404(Comment, comment_id)

    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Reply cannot be empty.'}), 400

    reply = Comment(
        user_id           = current_user.id,
        debate_id         = parent.debate_id,
        content           = content,
        parent_comment_id = parent.id,
    )

    # Award participation points for replying
    current_user.reputation_score += 10

    db.session.add(reply)
    db.session.commit()

    return jsonify({
        'success':    True,
        'comment_id': reply.id,
        'username':   current_user.username,
        'content':    reply.content,
        'created_at': reply.created_at.strftime('%d %b %Y, %H:%M'),
    })


@debates_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """
    Likes a comment. Awards +2 reputation to the comment's author.
    Rejects duplicate likes. Returns JSON.
    """
    comment = db.get_or_404(Comment, comment_id)

    existing = CommentLike.query.filter_by(
        user_id    = current_user.id,
        comment_id = comment_id
    ).first()

    if existing:
        return jsonify({'error': 'You have already liked this comment.'}), 400

    like = CommentLike(
        user_id    = current_user.id,
        comment_id = comment_id,
    )

    # Award reputation to the comment author (not the liker)
    comment.author.reputation_score += 2

    try:
        db.session.add(like)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'You have already liked this comment.'}), 400

    return jsonify({
        'success':    True,
        'like_count': len(comment.likes),
    })