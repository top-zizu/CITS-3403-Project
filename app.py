from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from models import db, User, Debate
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

# Register blueprints
app.register_blueprint(debates_bp)

# Database tables are managed by Flask-Migrate.
# Run `flask db upgrade` after cloning to create the schema.

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    form = SignupForm()

    if form.validate_on_submit():
        existing_username = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_username:
            flash("Username already taken.", "danger")
            return render_template("sign_up.html", form=form)

        if existing_email:
            flash("Email already registered.", "danger")
            return render_template("sign_up.html", form=form)

        user = User(
            username=form.username.data,
            email=form.email.data
        )
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


@app.route("/dashboard")
@login_required
def dashboard():
    debates = Debate.query.order_by(Debate.created_at.desc()).all()
    return render_template("dashboard.html", debates=debates)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        flash("If an account exists with that email, a reset link would be sent.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html", form=form)


@app.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(User.reputation_score.desc()).all()
    return render_template("leaderboard.html", users=users)

@app.route("/user/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    debates = Debate.query.filter_by(user_id=user.id).order_by(Debate.created_at.desc()).all()
    return render_template("profile.html", user=user, debates=debates)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        bio = request.form.get("bio", "").strip()

        if username and username != current_user.username:
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash("Username already taken.", "danger")
                return render_template("settings.html")
            current_user.username = username

        current_user.bio = bio
        current_user.is_public = request.form.get("is_public") == "on"
        current_user.notify_new_debates = request.form.get("notify_new_debates") == "on"
        current_user.notify_comments = request.form.get("notify_comments") == "on"
        current_user.notify_followed_accounts = request.form.get("notify_followed_accounts") == "on"

        db.session.commit()
        flash("Settings updated.", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html")


@app.route("/settings/password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("settings"))

    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "danger")
        return redirect(url_for("settings"))

    if new_password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("settings"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("settings"))

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "newest").strip()

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

    debates = debates.all()

    return render_template("searchdebates.html", debates=debates, query=query)

if __name__ == "__main__":
    app.run(debug=True)