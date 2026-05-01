from flask import Flask
from models import db

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///debate_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/")
def home():
    return "Debate app backend running"

if __name__ == "__main__":
    app.run(debug=True)