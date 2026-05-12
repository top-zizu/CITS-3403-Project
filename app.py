import os
from uuid import uuid4

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime, timezone, timedelta
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from models import db, User, Debate, Comment, Vote, Bookmark, Notification, DebateAccess
from forms import SignupForm, LoginForm, ForgotPasswordForm
from debates import debates_bp

app = Flask(__name__)
app.config.from_object("config.Config")

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DEBATE_TAGS = ["politics", "environment", "food", "lifestyle", "technology", "philosophy", "gaming"]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(debates_bp)


# ── Public pages ─────────────────────────────────────────────────

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route('/explore')
def explore():
    return render_template('explore.html')


def _ensure_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _time_until(expires_at):
    expires_at = _ensure_utc(expires_at)
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        return "Ended"

    remaining = expires_at - now
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    if days > 1:
        return f"Ends in {days} days"
    if days == 1:
        return "Ends in 1 day"
    if hours > 1:
        return f"Ends in {hours} hours"
    if hours == 1:
        return "Ends in 1 hour"
    if minutes > 1:
        return f"Ends in {minutes} minutes"
    return "Ends soon"


def _can_list_debate(debate):
    if not debate.is_private:
        return True
    if not current_user.is_authenticated:
        return False
    if debate.user_id == current_user.id:
        return True
    return DebateAccess.query.filter_by(
        debate_id=debate.id,
        user_id=current_user.id,
    ).first() is not None


def _allowed_avatar(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


def _save_avatar(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed_avatar(file_storage.filename):
        raise ValueError("Profile picture must be a PNG, JPG, GIF, or WebP image.")

    original = secure_filename(file_storage.filename)
    extension = original.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    upload_dir = os.path.join(app.static_folder, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    file_storage.save(os.path.join(upload_dir, filename))
    return url_for("static", filename=f"uploads/avatars/{filename}")


def _debate_to_dict(debate):
    total = debate.total_votes
    agree_pct = round((debate.agree_votes / total) * 100, 1) if total else 0
    disagree_pct = round((debate.disagree_votes / total) * 100, 1) if total else 0
    reveal_results = not debate.is_active

    user_vote = None
    is_bookmarked = False
    if current_user.is_authenticated:
        vote = Vote.query.filter_by(
            user_id=current_user.id,
            debate_id=debate.id,
        ).first()
        user_vote = vote.vote_type if vote else None
        is_bookmarked = Bookmark.query.filter_by(
            user_id=current_user.id,
            debate_id=debate.id,
        ).first() is not None

    return {
        "id": debate.id,
        "title": debate.title,
        "description": debate.description,
        "category": debate.category,
        "tags": [debate.category] if debate.category else [],
        "author": debate.display_author,
        "agree": debate.agree_votes,
        "disagree": debate.disagree_votes,
        "total_votes": total,
        "agree_pct": agree_pct,
        "disagree_pct": disagree_pct,
        "reveal_results": reveal_results,
        "comments": Comment.query.filter_by(debate_id=debate.id).count(),
        "is_active": debate.is_active,
        "is_private": debate.is_private,
        "status": "active" if debate.is_active else "ended",
        "timer": _time_until(debate.expires_at),
        "user_vote": user_vote,
        "saved": is_bookmarked,
        "url": url_for("debate_detail", debate_id=debate.id),
        "created_at": _ensure_utc(debate.created_at).isoformat(),
        "expires_at": _ensure_utc(debate.expires_at).isoformat(),
    }


def _comment_stance(comment):
    return comment.stance or "undecided"


def _sort_comments_for_discussion(comments, parent_stance=None):
    comments = list(comments)
    if parent_stance:
        different = [
            comment for comment in comments
            if _comment_stance(comment) != parent_stance
        ]
        same = [
            comment for comment in comments
            if _comment_stance(comment) == parent_stance
        ]
        return sorted(different, key=lambda c: len(c.likes), reverse=True) + sorted(same, key=lambda c: len(c.likes), reverse=True)
    return sorted(comments, key=lambda c: len(c.likes), reverse=True)


def _comment_to_dict(comment):
    stance = _comment_stance(comment)
    replies = _sort_comments_for_discussion(comment.replies, stance)
    return {
        "id": comment.id,
        "author": comment.author.username,
        "stance": stance,
        "time": comment.created_at.strftime("%d %b %Y, %H:%M"),
        "text": comment.content,
        "likes": len(comment.likes),
        "liked": (
            current_user.is_authenticated
            and any(like.user_id == current_user.id for like in comment.likes)
        ),
        "replies": [_comment_to_dict(reply) for reply in replies],
    }


@app.route("/api/debates")
def api_debates():
    query_text = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "newest").strip()

    debates = Debate.query

    if query_text:
        debates = debates.filter(
            or_(
                Debate.title.ilike(f"%{query_text}%"),
                Debate.description.ilike(f"%{query_text}%"),
            )
        )

    if category:
        debates = debates.filter(Debate.category == category)

    now = datetime.utcnow()
    if status == "active":
        debates = debates.filter(Debate.expires_at > now, Debate.is_closed == False)
    elif status in ("closed", "ended"):
        debates = debates.filter(
            or_(Debate.expires_at <= now, Debate.is_closed == True)
        )

    if sort == "votes":
        debates = debates.order_by((Debate.agree_votes + Debate.disagree_votes).desc())
    elif sort == "ending":
        debates = debates.filter(Debate.expires_at > now).order_by(Debate.expires_at.asc())
    else:
        debates = debates.order_by(Debate.created_at.desc())

    debates = [debate for debate in debates.limit(100).all() if _can_list_debate(debate)]
    categories = DEBATE_TAGS

    return jsonify({
        "debates": [_debate_to_dict(debate) for debate in debates],
        "categories": categories,
    })


@app.route("/api/trending-tags")
def api_trending_tags():
    now = datetime.utcnow()
    rows = (
        db.session.query(Debate.category, db.func.count(Debate.id))
        .filter(Debate.category.in_(DEBATE_TAGS))
        .filter(Debate.expires_at > now, Debate.is_closed == False)
        .group_by(Debate.category)
        .all()
    )
    counts = {category: count for category, count in rows}
    tags = sorted(DEBATE_TAGS, key=lambda tag: (-counts.get(tag, 0), tag))[:4]

    return jsonify({
        "tags": [{"tag": tag, "count": counts.get(tag, 0)} for tag in tags]
    })


@app.route("/api/dashboard")
@login_required
def api_dashboard():
    debate_count = Debate.query.filter_by(user_id=current_user.id).count()
    comment_count = Comment.query.filter_by(user_id=current_user.id).count()
    total_results = current_user.debates_won + current_user.debates_lost
    win_rate = round((current_user.debates_won / total_results) * 100) if total_results else 0

    return jsonify({
        "stats": {
            "points": current_user.reputation_score,
            "debates": debate_count,
            "comments": comment_count,
            "win_rate": win_rate,
        }
    })


@app.route("/api/me")
@login_required
def api_me():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "avatar": current_user.username[:1].upper(),
        "avatar_url": current_user.avatar_url,
        "profile_url": url_for("user_profile"),
        "reputation_score": current_user.reputation_score,
    })


# ── Auth ──────────────────────────────────────────────────────────

@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "danger")
            return render_template("sign_up.html", form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "danger")
            return render_template("sign_up.html", form=form)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("sign_up.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_input = form.login.data
        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username/email or password.", "danger")
            return render_template("login.html", form=form)
        login_user(user, remember=form.remember.data)
        flash("Logged in successfully.", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("homepage"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        flash("If an account exists with that email, a reset link would be sent.", "success")
        return redirect(url_for("login"))
    return render_template("forgot_password.html", form=form)


# ── Core pages ────────────────────────────────────────────────────

@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/search")
def search():
    return render_template("searchdebates.html")


# ── Debate detail ─────────────────────────────────────────────────

@app.route("/debate/<int:debate_id>")
def debate_detail(debate_id):
    from debates import close_debate
    debate = db.get_or_404(Debate, debate_id)

    # Private debate access gate
    if debate.is_private:
        if not current_user.is_authenticated:
            return redirect(url_for('debates.debate_access', debate_id=debate_id))
        if current_user.id != debate.user_id:
            has_access = DebateAccess.query.filter_by(
                user_id=current_user.id, debate_id=debate_id
            ).first()
            if not has_access:
                return redirect(url_for('debates.debate_access', debate_id=debate_id))

    if debate.is_active:
        vote_data = {"total": debate.total_votes, "revealed": False}
    else:
        if debate.winner is None:
            close_debate(debate)
        total = debate.total_votes
        if total == 0:
            vote_data = {
                "revealed": True, "total": 0,
                "agree_pct": 0, "disagree_pct": 0,
                "winner": debate.winner,
            }
        else:
            vote_data = {
                "revealed": True,
                "total": total,
                "agree": debate.agree_votes,
                "disagree": debate.disagree_votes,
                "agree_pct": round((debate.agree_votes / total) * 100, 1),
                "disagree_pct": round((debate.disagree_votes / total) * 100, 1),
                "winner": debate.winner,
            }

    top_level_comments = (
        Comment.query
        .filter_by(debate_id=debate_id, parent_comment_id=None)
        .all()
    )
    comment_tree = [
        _comment_to_dict(comment)
        for comment in _sort_comments_for_discussion(top_level_comments)
    ]

    user_vote = None
    is_bookmarked = False
    if current_user.is_authenticated:
        user_vote = Vote.query.filter_by(
            user_id=current_user.id, debate_id=debate_id
        ).first()
        is_bookmarked = Bookmark.query.filter_by(
            user_id=current_user.id, debate_id=debate_id
        ).first() is not None

    return render_template(
        "debate_detail.html",
        debate=debate,
        vote_data=vote_data,
        comments=top_level_comments,
        comment_tree=comment_tree,
        user_vote=user_vote,
        is_bookmarked=is_bookmarked,
    )


@app.route("/debates/<int:debate_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(debate_id):
    db.get_or_404(Debate, debate_id)
    existing = Bookmark.query.filter_by(
        user_id=current_user.id, debate_id=debate_id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"bookmarked": False})
    db.session.add(Bookmark(user_id=current_user.id, debate_id=debate_id))
    db.session.commit()
    return jsonify({"bookmarked": True})


# ── Leaderboard ───────────────────────────────────────────────────

@app.route("/leaderboard")
def leaderboard():
    """
    sort:   most_active (default) | most_distinctive | most_wins
    period: all_time (default)   | this_week        | this_month
    """
    sort   = request.args.get('sort', 'most_active')
    period = request.args.get('period', 'all_time')

    now   = datetime.now(timezone.utc)
    query = User.query

    if period in ('this_week', 'this_month'):
        days   = 7 if period == 'this_week' else 30
        cutoff = now - timedelta(days=days)

        voted_ids     = {v.user_id for v in Vote.query.filter(Vote.created_at    >= cutoff).all()}
        commented_ids = {c.user_id for c in Comment.query.filter(Comment.created_at >= cutoff).all()}
        created_ids   = {d.user_id for d in Debate.query.filter(Debate.created_at  >= cutoff).all()}
        active_ids    = voted_ids | commented_ids | created_ids

        if not active_ids:
            return render_template('leaderboard.html', users=[], sort=sort, period=period)

        query = query.filter(User.id.in_(active_ids))

    if sort == 'most_distinctive':
        query = query.order_by(User.conformity_score.asc())
    elif sort == 'most_wins':
        query = query.order_by(User.debates_won.desc())
    else:
        query = query.order_by(User.reputation_score.desc())

    return render_template('leaderboard.html', users=query.all(), sort=sort, period=period)


# ── Profile ───────────────────────────────────────────────────────

def _profile_context(user):
    """Build the context dict shared by both profile routes."""
    debates       = Debate.query.filter_by(user_id=user.id).order_by(Debate.created_at.desc()).all()
    vote_count    = Vote.query.filter_by(user_id=user.id).count()
    comment_count = Comment.query.filter_by(user_id=user.id).count()
    follower_count  = user.followers.count()
    following_count = user.following.count()
    is_following = False
    follows_you = False
    if current_user.is_authenticated and current_user.id != user.id:
        is_following = current_user.following.filter(User.id == user.id).first() is not None
        follows_you = user.following.filter(User.id == current_user.id).first() is not None
    recent_votes = (
        Vote.query
        .filter_by(user_id=user.id)
        .order_by(Vote.created_at.desc())
        .limit(5).all()
    )
    return dict(
        user=user,
        debates=debates,
        vote_count=vote_count,
        comment_count=comment_count,
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following,
        follows_you=follows_you,
        recent_votes=recent_votes,
    )


@app.route("/user-profile")
@login_required
def user_profile():
    return render_template("user-profile.html", **_profile_context(current_user))


@app.route("/user/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user-profile.html", **_profile_context(user))


# ── Settings ──────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        bio      = request.form.get("bio", "").strip()
        avatar = request.files.get("avatar")

        if username and username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash("Username already taken.", "danger")
                return render_template("settings.html")
            current_user.username = username

        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash("Email already in use.", "danger")
                return render_template("settings.html")
            current_user.email = email

        if avatar and avatar.filename:
            try:
                current_user.avatar_url = _save_avatar(avatar)
            except ValueError as error:
                flash(str(error), "danger")
                return render_template("settings.html")

        current_user.bio                        = bio
        current_user.is_public                  = request.form.get("is_public") == "on"
        current_user.notify_new_debates         = request.form.get("notify_new_debates") == "on"
        current_user.notify_comments            = request.form.get("notify_comments") == "on"
        current_user.notify_followed_accounts   = request.form.get("notify_followed_accounts") == "on"

        db.session.commit()
        flash("Settings updated.", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html")


@app.route("/settings/password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password", "")
    new_pw     = request.form.get("new_password", "")
    confirm_pw = request.form.get("confirm_password", "")

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "danger")
    elif len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "danger")
    elif new_pw != confirm_pw:
        flash("Passwords do not match.", "danger")
    else:
        current_user.set_password(new_pw)
        db.session.commit()
        flash("Password updated successfully.", "success")

    return redirect(url_for("settings"))


@app.route("/settings/delete", methods=["POST"])
@login_required
def delete_account():
    password = request.form.get("password", "")
    if not current_user.check_password(password):
        flash("Incorrect password. Account not deleted.", "danger")
        return redirect(url_for("settings"))
    db.session.delete(current_user)
    db.session.commit()
    flash("Your account has been deleted.", "info")
    return redirect(url_for("homepage"))


# ── Social ────────────────────────────────────────────────────────

@app.route("/notifications")
@login_required
def notifications():
    user_notifications = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", notifications=user_notifications)


@app.route("/friends")
@login_required
def friends():
    return render_template("friends.html")


def _social_user_to_dict(user):
    is_following = current_user.following.filter(User.id == user.id).first() is not None
    follows_you = user.following.filter(User.id == current_user.id).first() is not None
    debate_count = Debate.query.filter_by(user_id=user.id).count()

    return {
        "id": user.id,
        "username": user.username,
        "bio": user.bio or "",
        "avatar": user.username[:1].upper(),
        "avatar_url": user.avatar_url,
        "profile_url": url_for("profile", username=user.username),
        "follower_count": user.followers.count(),
        "following_count": user.following.count(),
        "debate_count": debate_count,
        "is_following": is_following,
        "follows_you": follows_you,
        "is_mutual": is_following and follows_you,
    }


@app.route("/api/friends")
@login_required
def api_friends():
    tab = request.args.get("tab", "following")
    query_text = request.args.get("q", "").strip()

    if tab == "requests":
        tab = "followers"

    if tab == "followers":
        users_query = current_user.followers.order_by(User.username.asc())
    elif tab == "discover":
        users_query = User.query.filter(User.id != current_user.id).order_by(User.username.asc())
    else:
        tab = "following"
        users_query = current_user.following.order_by(User.username.asc())

    if query_text:
        users_query = users_query.filter(User.username.ilike(f"%{query_text}%"))

    users = users_query.limit(50).all()
    if tab == "following":
        users.sort(
            key=lambda user: (
                user.following.filter(User.id == current_user.id).first() is None,
                user.username.lower(),
            )
        )
    elif tab == "discover" and not query_text:
        users = [
            user for user in users
            if current_user.following.filter(User.id == user.id).first() is not None
            and user.following.filter(User.id == current_user.id).first() is not None
        ]

    return jsonify({
        "tab": tab,
        "users": [_social_user_to_dict(user) for user in users],
        "counts": {
            "following": current_user.following.count(),
            "followers": current_user.followers.count(),
            "discover": User.query.filter(User.id != current_user.id).count(),
        },
    })


@app.route("/api/users/<int:user_id>/follow", methods=["POST", "DELETE"])
@login_required
def api_toggle_follow(user_id):
    user = db.get_or_404(User, user_id)

    if user.id == current_user.id:
        return jsonify({"error": "You cannot follow yourself."}), 400

    is_following = current_user.following.filter(User.id == user.id).first() is not None

    if request.method == "POST":
        if not is_following:
            current_user.following.append(user)
            if user.notify_followed_accounts:
                db.session.add(Notification(
                    user_id=user.id,
                    notification_type="social",
                    message=f"{current_user.username} started following you.",
                    link_url=url_for("profile", username=current_user.username),
                ))
            db.session.commit()
        return jsonify({"following": True, "user": _social_user_to_dict(user)})

    if is_following:
        current_user.following.remove(user)
        db.session.commit()

    return jsonify({"following": False, "user": _social_user_to_dict(user)})


# ── Debate lists ──────────────────────────────────────────────────

@app.route("/saved-debates")
@login_required
def saved_debates():
    bookmarks = (
        Bookmark.query
        .filter_by(user_id=current_user.id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    return render_template("saved_debates.html", debates=[b.debate for b in bookmarks])


@app.route("/my-debates")
@login_required
def my_debates():
    debates = (
        Debate.query
        .filter_by(user_id=current_user.id)
        .order_by(Debate.created_at.desc())
        .all()
    )
    return render_template("my_debates.html", debates=debates)


if __name__ == "__main__":
    app.run(debug=True)
