import pytest
import sqlalchemy as sa
from datetime import datetime, timezone, timedelta
from app import app as flask_app
from models import db, User, Debate, Vote, Comment, Notification


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    test_engine = sa.create_engine("sqlite:///:memory:")

    with flask_app.app_context():
        db.session.remove()
        flask_app.extensions["sqlalchemy"].engines[None] = test_engine
        db.Model.metadata.create_all(test_engine)
        yield flask_app
        db.session.remove()
        db.Model.metadata.drop_all(test_engine)
        test_engine.dispose()


@pytest.fixture
def sample_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_debate(app, sample_user):
    debate = Debate(
        title="Test Debate",
        description="This is a test debate.",
        category="general",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        user_id=sample_user.id,
    )
    db.session.add(debate)
    db.session.commit()
    return debate


# ── User model tests ──────────────────────────────────────────────

def test_password_hashing(app, sample_user):
    """Password is hashed and can be verified correctly."""
    assert sample_user.check_password("password123") is True


def test_wrong_password_rejected(app, sample_user):
    """Wrong password returns False."""
    assert sample_user.check_password("wrongpassword") is False


def test_password_hash_not_plaintext(app, sample_user):
    """Password hash is not stored as plaintext."""
    assert sample_user.password_hash != "password123"


def test_user_default_reputation(app, sample_user):
    """New users start with 0 reputation."""
    assert sample_user.reputation_score == 0


def test_user_default_notifications_enabled(app, sample_user):
    """Notification preferences default to True."""
    assert sample_user.notify_new_debates is True
    assert sample_user.notify_comments is True
    assert sample_user.notify_followed_accounts is True


# ── Debate model tests ────────────────────────────────────────────

def test_debate_is_active(app, sample_debate):
    """A debate with a future expiry is active."""
    assert sample_debate.is_active is True


def test_debate_is_inactive_when_expired(app, sample_user):
    """A debate with a past expiry is not active."""
    debate = Debate(
        title="Expired Debate",
        description="This debate has ended.",
        category="general",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        user_id=sample_user.id,
    )
    db.session.add(debate)
    db.session.commit()
    assert debate.is_active is False


def test_debate_total_votes(app, sample_debate):
    """Total votes is the sum of agree and disagree votes."""
    sample_debate.agree_votes = 5
    sample_debate.disagree_votes = 3
    db.session.commit()
    assert sample_debate.total_votes == 8


def test_debate_display_author_anonymous(app, sample_debate):
    """Anonymous debates show 'Anonymous' as the author."""
    sample_debate.is_anonymous = True
    db.session.commit()
    assert sample_debate.display_author == "Anonymous"


def test_debate_display_author_named(app, sample_debate):
    """Non-anonymous debates show the author's username."""
    sample_debate.is_anonymous = False
    db.session.commit()
    assert sample_debate.display_author == "testuser"


# ── Vote model tests ──────────────────────────────────────────────

def test_vote_recorded(app, sample_user, sample_debate):
    """A vote is correctly saved to the database."""
    vote = Vote(
        user_id=sample_user.id,
        debate_id=sample_debate.id,
        vote_type="agree",
    )
    db.session.add(vote)
    db.session.commit()
    saved = Vote.query.filter_by(user_id=sample_user.id, debate_id=sample_debate.id).first()
    assert saved is not None
    assert saved.vote_type == "agree"


def test_duplicate_vote_rejected(app, sample_user, sample_debate):
    """A user cannot vote twice on the same debate."""
    from sqlalchemy.exc import IntegrityError
    v1 = Vote(user_id=sample_user.id, debate_id=sample_debate.id, vote_type="agree")
    v2 = Vote(user_id=sample_user.id, debate_id=sample_debate.id, vote_type="disagree")
    db.session.add(v1)
    db.session.commit()
    db.session.add(v2)
    with pytest.raises(IntegrityError):
        db.session.commit()


# ── Follow system tests ───────────────────────────────────────────

def test_follow_user(app, sample_user):
    """A user can follow another user."""
    other = User(username="otheruser", email="other@example.com")
    other.set_password("password123")
    db.session.add(other)
    db.session.commit()
    sample_user.following.append(other)
    db.session.commit()
    assert sample_user.following.filter_by(id=other.id).first() is not None


def test_unfollow_user(app, sample_user):
    """A user can unfollow another user."""
    other = User(username="otheruser2", email="other2@example.com")
    other.set_password("password123")
    db.session.add(other)
    db.session.commit()
    sample_user.following.append(other)
    db.session.commit()
    sample_user.following.remove(other)
    db.session.commit()
    assert sample_user.following.filter_by(id=other.id).first() is None


# ── Notification model tests ──────────────────────────────────────

def test_notification_created(app, sample_user):
    """A notification can be created and retrieved for a user."""
    notif = Notification(
        user_id=sample_user.id,
        notification_type="social",
        message="Someone followed you.",
    )
    db.session.add(notif)
    db.session.commit()
    saved = Notification.query.filter_by(user_id=sample_user.id).first()
    assert saved is not None
    assert saved.message == "Someone followed you."
    assert saved.is_read is False
