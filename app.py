from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
from debates import debates_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///debate_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialise extensions
db.init_app(app)
migrate = Migrate(app, db)

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(debates_bp)
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "Debate app backend running"

if __name__ == "__main__":
    app.run(debug=True)