from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, User, Debate
from forms import SignupForm, LoginForm, ForgotPasswordForm
from debates import debates_bp

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-secret-key-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///debate_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(debates_bp)

with app.app_context():
    db.create_all()

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


if __name__ == "__main__":
    app.run(debug=True)