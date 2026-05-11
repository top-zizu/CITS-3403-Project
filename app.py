from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime, timezone, timedelta
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from models import db, User, Debate, Comment, Vote, Bookmark, Notification
from forms import SignupForm, LoginForm, ForgotPasswordForm
from debates import debates_bp

app = Flask(__name__)
app.config.from_object("config.Config")

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

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
    debates = Debate.query.order_by(Debate.created_at.desc()).all()
    return render_template("dashboard.html", debates=debates)


@app.route("/search")
def search():
    query    = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    status   = request.args.get("status", "").strip()
    sort     = request.args.get("sort", "newest").strip()

    debates = Debate.query
    if query:
        debates = debates.filter(
            (Debate.title.ilike(f"%{query}%")) |
            (Debate.description.ilike(f"%{query}%"))
        )
    if category:
        debates = debates.filter(Debate.category == category)

    now = datetime.utcnow()
    if status == "active":
        debates = debates.filter(Debate.expires_at > now, Debate.is_closed == False)
    elif status == "closed":
        debates = debates.filter(
            (Debate.expires_at <= now) | (Debate.is_closed == True)
        )
    if sort == "votes":
        debates = debates.order_by(
            (Debate.agree_votes + Debate.disagree_votes).desc()
        )
    elif sort == "ending":
        debates = debates.filter(Debate.expires_at > now).order_by(Debate.expires_at.asc())
    else:
        debates = debates.order_by(Debate.created_at.desc())

    return render_template("searchdebates.html", debates=debates.all(), query=query)


# ── Debate detail ─────────────────────────────────────────────────

@app.route("/debate/<int:debate_id>")
def debate_detail(debate_id):
    from debates import close_debate
    debate = db.get_or_404(Debate, debate_id)

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
        .order_by(Comment.created_at.asc())
        .all()
    )

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