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

@app.route("/api/debates/<int:debate_id>/comments")
def api_debate_comments(debate_id):
    db.get_or_404(Debate, debate_id)
    sort = request.args.get("sort", "newest")

    if sort == "top":
        top_level = (
            Comment.query
            .filter_by(debate_id=debate_id, parent_comment_id=None)
            .all()
        )
        top_level.sort(key=lambda c: len(c.likes), reverse=True)
    else:
        top_level = (
            Comment.query
            .filter_by(debate_id=debate_id, parent_comment_id=None)
            .order_by(Comment.created_at.asc())
            .all()
        )

    all_author_ids = {c.user_id for c in top_level}
    for c in top_level:
        for r in c.replies:
            all_author_ids.add(r.user_id)

    votes_on_debate = Vote.query.filter_by(debate_id=debate_id).filter(
        Vote.user_id.in_(all_author_ids)
    ).all()
    stance_map = {'agree': 'blue', 'disagree': 'red'}
    comment_stances = {v.user_id: stance_map.get(v.vote_type, 'neutral') for v in votes_on_debate}

    def comment_to_dict(c):
        return {
            "id": c.id,
            "author": c.author.username,
            "stance": comment_stances.get(c.user_id, 'neutral'),
            "time": c.created_at.strftime('%d %b %Y, %H:%M'),
            "text": c.content,
            "likes": len(c.likes),
            "replies": [comment_to_dict(r) for r in c.replies],
        }

    return jsonify({
        "comments": [comment_to_dict(c) for c in top_level],
        "sort": sort,
    })

@app.route("/api/debates")
def api_debates():
    query_text = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "newest").strip()

    filter_type = request.args.get("filter", "").strip()

    debates = Debate.query

    if filter_type == "interacted" and current_user.is_authenticated:
        voted_ids    = {v.debate_id for v in Vote.query.filter_by(user_id=current_user.id).all()}
        commented_ids = {c.debate_id for c in Comment.query.filter_by(user_id=current_user.id).all()}
        created_ids  = {d.id for d in Debate.query.filter_by(user_id=current_user.id).all()}
        interacted_ids = voted_ids | commented_ids | created_ids
        debates = debates.filter(Debate.id.in_(interacted_ids))

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
    categories = sorted({debate.category for debate in debates if debate.category})

    return jsonify({
        "debates": [_debate_to_dict(debate) for debate in debates],
        "categories": categories,
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
    return render_template("home.html", username=current_user.username)


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

    is_author = current_user.is_authenticated and current_user.id == debate.user_id
    if debate.is_active and not is_author:
        vote_data = {"total": debate.total_votes, "revealed": False}
    elif debate.is_active and is_author:
        total = debate.total_votes
        vote_data = {
            "revealed": True,
            "total": total,
            "agree": debate.agree_votes,
            "disagree": debate.disagree_votes,
            "agree_pct": round((debate.agree_votes / total) * 100, 1) if total else 0,
            "disagree_pct": round((debate.disagree_votes / total) * 100, 1) if total else 0,
            "winner": None,
        }
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

    sort = request.args.get('sort', 'newest')
    if sort == 'top':
        top_level_comments = (
            Comment.query
            .filter_by(debate_id=debate_id, parent_comment_id=None)
            .all()
        )
        top_level_comments.sort(key=lambda c: len(c.likes), reverse=True)
    else:
        top_level_comments = (
            Comment.query
            .filter_by(debate_id=debate_id, parent_comment_id=None)
            .order_by(Comment.created_at.asc())
            .all()
        )

    # Build stance map: commenter user_id -> 'blue'|'red'|'neutral'
    all_author_ids = {c.user_id for c in top_level_comments}
    for c in top_level_comments:
        for r in c.replies:
            all_author_ids.add(r.user_id)

    votes_on_debate = Vote.query.filter_by(debate_id=debate_id).filter(
        Vote.user_id.in_(all_author_ids)
    ).all()
    stance_map = {'agree': 'blue', 'disagree': 'red'}
    comment_stances = {v.user_id: stance_map.get(v.vote_type, 'neutral') for v in votes_on_debate}

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
        user_vote=user_vote,
        is_bookmarked=is_bookmarked,
        comment_stances=comment_stances,
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
    for n in user_notifications:
        n.is_read = True
    db.session.commit()
    return render_template("notifications.html", notifications=user_notifications)


@app.route("/api/notifications/unread-count")
@login_required
def api_notifications_unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False,
    ).count()
    return jsonify({"count": count})


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


@app.route("/api/activity/friends")
@login_required
def api_activity_friends():
    following = current_user.following.all()
    if not following:
        return jsonify({"activities": []})

    following_ids = [u.id for u in following]
    following_map = {u.id: u.username for u in following}

    activities = []

    recent_votes = (
        Vote.query
        .filter(Vote.user_id.in_(following_ids))
        .order_by(Vote.created_at.desc())
        .limit(20).all()
    )
    for v in recent_votes:
        activities.append({
            "username": following_map[v.user_id],
            "type": "vote",
            "debate_title": v.debate.title,
            "debate_url": url_for("debate_detail", debate_id=v.debate_id),
            "created_at": v.created_at,
        })

    recent_comments = (
        Comment.query
        .filter(Comment.user_id.in_(following_ids))
        .order_by(Comment.created_at.desc())
        .limit(20).all()
    )
    for c in recent_comments:
        activities.append({
            "username": following_map[c.user_id],
            "type": "comment",
            "debate_title": c.debate.title,
            "debate_url": url_for("debate_detail", debate_id=c.debate_id),
            "created_at": c.created_at,
        })

    recent_debates = (
        Debate.query
        .filter(Debate.user_id.in_(following_ids))
        .order_by(Debate.created_at.desc())
        .limit(20).all()
    )
    for d in recent_debates:
        activities.append({
            "username": following_map[d.user_id],
            "type": "create",
            "debate_title": d.title,
            "debate_url": url_for("debate_detail", debate_id=d.id),
            "created_at": d.created_at,
        })

    activities.sort(key=lambda x: x["created_at"], reverse=True)
    for a in activities:
        del a["created_at"]

    return jsonify({"activities": activities[:20]})

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
