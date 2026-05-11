from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# -------------------------
# FOLLOW SYSTEM
# -------------------------

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)


# -------------------------
# USER
# -------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    avatar_url = db.Column(db.String(300), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    reputation_score = db.Column(db.Integer, default=0)
    currency_balance = db.Column(db.Integer, default=0)

    debates_won = db.Column(db.Integer, default=0)
    debates_lost = db.Column(db.Integer, default=0)
    conformity_score = db.Column(db.Float, default=0.0)

    is_public = db.Column(db.Boolean, default=True)

    notify_new_debates = db.Column(db.Boolean, default=True)
    notify_comments = db.Column(db.Boolean, default=True)
    notify_followed_accounts = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    debates = db.relationship("Debate", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    votes = db.relationship("Vote", backref="user", lazy=True)

    following = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# -------------------------
# DEBATE
# -------------------------

class Debate(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(50), nullable=False)

    is_private = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)

    image_url = db.Column(db.String(300), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    is_closed = db.Column(db.Boolean, default=False)

    agree_votes = db.Column(db.Integer, default=0)
    disagree_votes = db.Column(db.Integer, default=0)

    winner = db.Column(db.String(20), nullable=True)  
    # "agree", "disagree", "draw", or None while active

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    comments = db.relationship("Comment", backref="debate", lazy=True, cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="debate", lazy=True, cascade="all, delete-orphan")
    bookmarks = db.relationship("Bookmark", backref="debate", lazy=True, cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="debate", lazy=True, cascade="all, delete-orphan")
    reopen_votes = db.relationship("ReopenVote", backref="debate", lazy=True, cascade="all, delete-orphan")

    @property
    def total_votes(self):
        return self.agree_votes + self.disagree_votes

    @property
    def is_active(self):
        return datetime.now(timezone.utc) < self.expires_at and not self.is_closed


# -------------------------
# PRIVATE DEBATE ACCESS
# -------------------------

class DebateAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    debate_id = db.Column(db.Integer, db.ForeignKey("debate.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# -------------------------
# VOTES
# -------------------------

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    vote_type = db.Column(db.String(20), nullable=False)
    # "agree" or "disagree"

    hide_vote_from_profile = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    debate_id = db.Column(db.Integer, db.ForeignKey("debate.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "debate_id", name="unique_user_vote_per_debate"),
    )


# -------------------------
# COMMENTS + THREADED REPLIES
# -------------------------

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    debate_id = db.Column(db.Integer, db.ForeignKey("debate.id"), nullable=False)

    parent_comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)

    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        lazy=True
    )

    likes = db.relationship("CommentLike", backref="comment", lazy=True, cascade="all, delete-orphan")


class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("user_id", "comment_id", name="unique_user_comment_like"),
    )


# -------------------------
# BOOKMARK / FLAG TO TRACK
# -------------------------

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    debate_id = db.Column(db.Integer, db.ForeignKey("debate.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("user_id", "debate_id", name="unique_user_bookmark"),
    )


# -------------------------
# REPORTS
# -------------------------

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reason = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    debate_id = db.Column(db.Integer, db.ForeignKey("debate.id"), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)


# -------------------------
# NOTIFICATIONS
# -------------------------

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    message = db.Column(db.String(300), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    link_url = db.Column(db.String(300), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# -------------------------
# REOPEN CLOSED DEBATES
# -------------------------

class ReopenVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    debate_id = db.Column(db.Integer, db.ForeignKey("debate.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("user_id", "debate_id", name="unique_user_reopen_vote"),
    )


# -------------------------
# CATEGORIES
# -------------------------

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)