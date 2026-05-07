# ============================================================
# Covers: debate create/view/list, voting, comments
# ============================================================
# SETUP REQUIRED IN app.py :
#   from debates import debates_bp
#   app.register_blueprint(debates_bp)
# ============================================================

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
from models import db, Debate, Vote, Comment, CommentLike

debates_bp = Blueprint('debates', __name__)
def close_debate(debate):
    """
    Declares the winner of an expired debate and updates
    reputation scores for all users who voted.
    Only runs once — skipped if winner is already set.
    """
    if debate.winner is not None:
        return  # Already closed, nothing to do

    # --- Determine winner ---
    if debate.agree_votes > debate.disagree_votes:
        debate.winner = 'agree'
    elif debate.disagree_votes > debate.agree_votes:
        debate.winner = 'disagree'
    else:
        debate.winner = 'draw'

    # --- Update stats for every user who voted ---
    for vote in debate.votes:
        voter = vote.user
        if debate.winner == 'draw':
            # Draw — no change to won/lost but small reputation gain for participating
            voter.reputation_score += 1
        elif vote.vote_type == debate.winner:
            # Voted on the winning side
            voter.debates_won += 1
            voter.reputation_score += 10
        else:
            # Voted on the losing side
            voter.debates_lost += 1
            voter.reputation_score = max(0, voter.reputation_score - 5)

    db.session.commit()


# ============================================================
# DEBATE ROUTES
# ============================================================

@debates_bp.route('/debates/create', methods=['GET', 'POST'])
@login_required
def create_debate():
    """
    GET  — render the create debate form
    POST — validate input, save debate to DB, redirect to the new debate page
    """
    if request.method == 'GET':
        return render_template('create_debate.html')

    # --- Pull values from the submitted form ---
    title        = request.form.get('title', '').strip()
    description  = request.form.get('description', '').strip()
    category     = request.form.get('category', '').strip()
    is_anonymous = request.form.get('is_anonymous') == 'on'
    is_private   = request.form.get('is_private') == 'on'

    # duration_days comes from a dropdown (e.g. 1, 3, 7, 14)
    try:
        duration_days = int(request.form.get('duration_days', 1))
    except ValueError:
        duration_days = 1

    # --- Basic validation ---
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

    # --- Build and save the debate ---
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

    db.session.add(debate)
    db.session.commit()

    return redirect(url_for('debates.view_debate', debate_id=debate.id))


@debates_bp.route('/debates/<int:debate_id>')
def view_debate(debate_id):
    """
    Displays a single debate page.
    Vote distribution is hidden while the debate is active.
    Full results are shown after expiry.
    """
    debate = db.get_or_404(Debate, debate_id)

    # --- Vote summary: hide breakdown while active ---
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
                'revealed':    True,
                'total':       0,
                'agree_pct':   0,
                'disagree_pct': 0,
                'winner':      debate.winner,
            }
        else:
            vote_data = {
                'revealed':    True,
                'total':       total,
                'agree':       debate.agree_votes,
                'disagree':    debate.disagree_votes,
                'agree_pct':   round((debate.agree_votes / total) * 100, 1),
                'disagree_pct': round((debate.disagree_votes / total) * 100, 1),
                'winner':      debate.winner,
            }
    # --- Get top-level comments (replies load via comment.replies in template) ---
    top_level_comments = Comment.query.filter_by(
        debate_id=debate_id,
        parent_comment_id=None
    ).order_by(Comment.created_at.asc()).all()

    # --- Check if current user has already voted ---
    user_vote = None
    if current_user.is_authenticated:
        user_vote = Vote.query.filter_by(
            user_id=current_user.id,
            debate_id=debate_id
        ).first()

    return render_template(
        'debate.html',
        debate         = debate,
        vote_data      = vote_data,
        comments       = top_level_comments,
        user_vote      = user_vote,
    )


@debates_bp.route('/debates')
def debate_list():
    """
    Returns a list of all debates for the dashboard feed.
    Ordered newest first.
    """
    debates = Debate.query.order_by(Debate.created_at.desc()).all()
    return render_template('dashboard.html', debates=debates)


# ============================================================
# VOTING ROUTES
# ============================================================

@debates_bp.route('/debates/<int:debate_id>/vote', methods=['POST'])
@login_required
def cast_vote(debate_id):
    """
    Records an Agree or Disagree vote.
    Rules enforced:
      - Debate must still be active
      - One vote per user per debate (UniqueConstraint handles this at DB level too)
    Returns JSON so this can be called via AJAX.
    """
    debate = db.get_or_404(Debate, debate_id)

    if not debate.is_active:
        return jsonify({'error': 'This debate has closed — voting is no longer allowed.'}), 400

    vote_type = request.form.get('vote_type', '').lower()
    if vote_type not in ('agree', 'disagree'):
        return jsonify({'error': 'Invalid vote type. Must be agree or disagree.'}), 400

    # Check for duplicate vote before hitting the DB constraint
    existing = Vote.query.filter_by(
        user_id=current_user.id,
        debate_id=debate_id
    ).first()

    if existing:
        return jsonify({'error': 'You have already voted on this debate.'}), 400

    # --- Save vote and update debate counters ---
    vote = Vote(
        user_id   = current_user.id,
        debate_id = debate_id,
        vote_type = vote_type,
    )

    if vote_type == 'agree':
        debate.agree_votes += 1
    else:
        debate.disagree_votes += 1

    try:
        db.session.add(vote)
        db.session.commit()
    except IntegrityError:
        # Catches race condition where two requests slip past the duplicate check
        db.session.rollback()
        return jsonify({'error': 'You have already voted on this debate.'}), 400

    return jsonify({
        'success': True,
        'total':   debate.total_votes,
    })


# ============================================================
# COMMENT ROUTES
# ============================================================

@debates_bp.route('/debates/<int:debate_id>/comments', methods=['POST'])
@login_required
def post_comment(debate_id):
    """
    Posts a top-level comment on a debate (parent_comment_id = None).
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
    Posts a reply to an existing comment (sets parent_comment_id).
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
    Likes a comment. Rejects duplicate likes.
    Returns JSON with updated like count.
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
