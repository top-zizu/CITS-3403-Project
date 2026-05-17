# ============================================================
# debates.py
# Covers: debate create/view/list, voting, comments,
#         private debate access, delete
# ============================================================
# Scoring system:
#   +20  reputation for creating a debate
#   +5   reputation for casting a vote
#   +10  reputation for posting a comment or reply
#   +2   reputation awarded to comment author when their comment is liked
#   Conformity score: % of a user's votes that matched the winning side
#                     (recalculated on debate close, draws excluded)
# ============================================================

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
import secrets
from models import db, Debate, Vote, Comment, CommentLike, Bookmark, DebateAccess, Notification

debates_bp = Blueprint('debates', __name__)


def close_debate(debate):
    """
    Declares the winner of an expired debate.
    Updates debates_won / debates_lost for all voters.
    Recalculates conformity_score for each voter.
    Only runs once — skipped if winner is already set.
    """
    if debate.winner is not None:
        return

    if debate.agree_votes > debate.disagree_votes:
        debate.winner = 'agree'
    elif debate.disagree_votes > debate.agree_votes:
        debate.winner = 'disagree'
    else:
        debate.winner = 'draw'

    debate.is_closed = True

    if debate.winner != 'draw':
        for vote in debate.votes:
            if vote.vote_type == debate.winner:
                vote.user.debates_won += 1
            else:
                vote.user.debates_lost += 1

        for vote in debate.votes:
            user = vote.user

            total = (
                db.session.query(Vote)
                .join(Debate, Vote.debate_id == Debate.id)
                .filter(Vote.user_id == user.id)
                .filter(Debate.winner.isnot(None))
                .filter(Debate.winner != 'draw')
                .count()
            )

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

    # Notify all voters that the debate has closed
    for vote in debate.votes:
        if vote.user_id != debate.user_id:
            result = debate.winner.capitalize() if debate.winner != 'draw' else 'a Draw'
            outcome = 'won' if vote.vote_type == debate.winner else 'lost'
            if debate.winner == 'draw':
                outcome = 'drew'
            db.session.add(Notification(
                user_id=vote.user_id,
                notification_type="debate_closed",
                message=f"A debate you voted on has closed: \"{debate.title}\" — {result}. You {outcome}.",
                link_url=url_for("debate_detail", debate_id=debate.id),
            ))

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
        access_code  = secrets.token_hex(3) if is_private else None,
        user_id      = current_user.id,
    )

    current_user.reputation_score += 20

    db.session.add(debate)
    db.session.commit()

    if is_private:
        flash(f'Your debate is private. Share this access code: {debate.access_code}', 'info')

    return redirect(url_for('debate_detail', debate_id=debate.id))


@debates_bp.route('/debates/<int:debate_id>')
def view_debate(debate_id):
    """Redirects to the main styled debate detail page."""
    return redirect(url_for('debate_detail', debate_id=debate_id))


@debates_bp.route('/debates')
def debate_list():
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
    Returns JSON for AJAX calls.
    """
    debate = db.get_or_404(Debate, debate_id)

    if not debate.is_active:
        return jsonify({'error': 'This debate has closed — voting is no longer allowed.'}), 400

    vote_type = request.form.get('vote_type', '').lower()
    if vote_type not in ('agree', 'disagree'):
        return jsonify({'error': 'Invalid vote type. Must be agree or disagree.'}), 400

    existing = Vote.query.filter_by(
        user_id=current_user.id, debate_id=debate_id
    ).first()

    if existing:
        if existing.vote_type == vote_type:
            if vote_type == 'agree':
                debate.agree_votes -= 1
            else:
                debate.disagree_votes -= 1

            current_user.reputation_score = max(0, current_user.reputation_score - 5)
            db.session.delete(existing)
            db.session.commit()

            return jsonify({'success': True, 'removed': True, 'total': debate.total_votes})

        # Reverse the old counter, apply the new one
        if existing.vote_type == 'agree':
            debate.agree_votes -= 1
        else:
            debate.disagree_votes -= 1

        if vote_type == 'agree':
            debate.agree_votes += 1
        else:
            debate.disagree_votes += 1

        existing.vote_type = vote_type
        db.session.commit()

        return jsonify({'success': True, 'changed': True, 'removed': False, 'total': debate.total_votes})

    # First-time vote
    vote = Vote(
        user_id=current_user.id,
        debate_id=debate_id,
        vote_type=vote_type,
    )

    if vote_type == 'agree':
        debate.agree_votes += 1
    else:
        debate.disagree_votes += 1

    current_user.reputation_score += 5

    try:
        db.session.add(vote)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Vote could not be saved. Please refresh and try again.'}), 400

    return jsonify({'success': True, 'changed': False, 'removed': False, 'total': debate.total_votes})


# ============================================================
# COMMENTS
# ============================================================

def _comment_stance_for_user(user_id, debate_id):
    user_vote = Vote.query.filter_by(user_id=user_id, debate_id=debate_id).first()
    stance_map = {'agree': 'blue', 'disagree': 'red'}
    return stance_map.get(user_vote.vote_type, 'neutral') if user_vote else 'neutral'


@debates_bp.route('/debates/<int:debate_id>/comments', methods=['POST'])
@login_required
def post_comment(debate_id):
    """Posts a top-level comment. Awards +10 reputation. Returns JSON."""
    db.get_or_404(Debate, debate_id)

    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Comment cannot be empty.'}), 400

    stance = _comment_stance_for_user(current_user.id, debate_id)
    comment = Comment(
        user_id=current_user.id,
        debate_id=debate_id,
        content=content,
        stance=stance,
        parent_comment_id=None,
    )

    current_user.reputation_score += 10

    db.session.add(comment)
    db.session.flush()

    # Notify the debate author if someone else comments on their debate
    debate = db.get_or_404(Debate, debate_id)
    if debate.user_id != current_user.id:
        db.session.add(Notification(
            user_id=debate.user_id,
            notification_type="comment",
            message=f"{current_user.username} commented on your debate: \"{debate.title}\"",
            link_url=url_for("debate_detail", debate_id=debate_id),
        ))

    db.session.commit()

    return jsonify({
        'success':    True,
        'comment_id': comment.id,
        'username':   current_user.username,
        'content':    comment.content,
        'created_at': comment.created_at.strftime('%d %b %Y, %H:%M'),
        'stance':     comment.stance,
    })


@debates_bp.route('/comments/<int:comment_id>/reply', methods=['POST'])
@login_required
def post_reply(comment_id):
    """Posts a reply to an existing comment. Awards +10 reputation. Returns JSON."""
    parent = db.get_or_404(Comment, comment_id)

    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Reply cannot be empty.'}), 400

    stance = _comment_stance_for_user(current_user.id, parent.debate_id)
    reply = Comment(
        user_id=current_user.id,
        debate_id=parent.debate_id,
        content=content,
        stance=stance,
        parent_comment_id=parent.id,
    )

    current_user.reputation_score += 10

    db.session.add(reply)
    db.session.flush()

    # Notify the parent comment author if someone else replies to them
    if parent.user_id != current_user.id:
        db.session.add(Notification(
            user_id=parent.user_id,
            notification_type="reply",
            message=f"{current_user.username} replied to your comment on \"{parent.debate.title}\"",
            link_url=url_for("debate_detail", debate_id=parent.debate_id),
        ))

    db.session.commit()

    return jsonify({
        'success':    True,
        'comment_id': reply.id,
        'username':   current_user.username,
        'content':    reply.content,
        'created_at': reply.created_at.strftime('%d %b %Y, %H:%M'),
        'stance':     reply.stance,
    })


@debates_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """Likes a comment. Awards +2 reputation to the author. Returns JSON."""
    comment = db.get_or_404(Comment, comment_id)

    existing = CommentLike.query.filter_by(
        user_id=current_user.id,
        comment_id=comment_id
    ).first()

    if existing:
        return jsonify({'error': 'You have already liked this comment.'}), 400

    like = CommentLike(user_id=current_user.id, comment_id=comment_id)
    comment.author.reputation_score += 2

    try:
        db.session.add(like)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'You have already liked this comment.'}), 400

    return jsonify({'success': True, 'like_count': len(comment.likes)})


# ============================================================
# PRIVATE DEBATE ACCESS
# ============================================================

@debates_bp.route('/debates/<int:debate_id>/access', methods=['GET', 'POST'])
def debate_access(debate_id):
    """
    Code-entry gate for private debates.
    GET  — show the access form.
    POST — validate the code, grant access if correct.
    """
    debate = db.get_or_404(Debate, debate_id)

    if not debate.is_private:
        return redirect(url_for('debate_detail', debate_id=debate_id))

    if current_user.is_authenticated and current_user.id == debate.user_id:
        return redirect(url_for('debate_detail', debate_id=debate_id))

    error = None

    if request.method == 'POST':
        entered_code = request.form.get('access_code', '').strip()

        if entered_code == debate.access_code:
            if not current_user.is_authenticated:
                flash('Please log in to access this private debate.', 'warning')
                return redirect(url_for('login'))

            existing = DebateAccess.query.filter_by(
                user_id=current_user.id,
                debate_id=debate_id
            ).first()
            if not existing:
                db.session.add(DebateAccess(
                    user_id=current_user.id,
                    debate_id=debate_id
                ))
                db.session.commit()

            return redirect(url_for('debate_detail', debate_id=debate_id))

        error = 'Incorrect access code. Please try again.'

    return render_template('debate_access.html', debate=debate, error=error)


# ============================================================
# DELETE DEBATE
# ============================================================

@debates_bp.route('/debates/<int:debate_id>/delete', methods=['POST'])
@login_required
def delete_debate(debate_id):
    """
    Permanently deletes a debate and all related data.
    Only the debate's author can delete it. Returns JSON.
    """
    debate = db.get_or_404(Debate, debate_id)

    if debate.user_id != current_user.id:
        return jsonify({'error': 'You can only delete your own debates.'}), 403

    db.session.delete(debate)
    db.session.commit()
    return jsonify({'success': True})
