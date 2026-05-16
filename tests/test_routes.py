import pytest
import sqlalchemy as sa
from datetime import datetime, timezone, timedelta
from app import app as flask_app
from models import db, User, Debate, Vote, Comment, Bookmark


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
def client(app):
    return app.test_client()


@pytest.fixture
def sample_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_client(client, sample_user):
    client.post("/login", data={
        "login": "testuser",
        "password": "password123",
    }, follow_redirects=True)
    return client


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


# ── Public page tests ─────────────────────────────────────────────

def test_homepage_loads(client):
    """Homepage is accessible without login."""
    response = client.get("/")
    assert response.status_code == 200


def test_explore_page_loads(client):
    """Explore page is accessible without login."""
    response = client.get("/explore")
    assert response.status_code == 200


def test_login_page_loads(client):
    """Login page renders correctly."""
    response = client.get("/login")
    assert response.status_code == 200


def test_signup_page_loads(client):
    """Sign up page renders correctly."""
    response = client.get("/sign-up")
    assert response.status_code == 200


# ── Auth tests ────────────────────────────────────────────────────

def test_signup_creates_user(client, app):
    """A new user can register successfully."""
    response = client.post("/sign-up", data={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepass123",
        "confirm_password": "securepass123",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None


def test_login_valid_credentials(client, sample_user):
    """A user can log in with correct credentials."""
    response = client.post("/login", data={
        "login": "testuser",
        "password": "password123",
    }, follow_redirects=True)
    assert response.status_code == 200


def test_login_invalid_password(client, sample_user):
    """Login fails with wrong password."""
    response = client.post("/login", data={
        "login": "testuser",
        "password": "wrongpassword",
    }, follow_redirects=True)
    assert b"Invalid" in response.data


def test_logout_redirects(logged_in_client):
    """Logging out redirects to homepage."""
    response = logged_in_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302


def test_dashboard_requires_login(client):
    """Dashboard redirects unauthenticated users to login."""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ── Debate tests ──────────────────────────────────────────────────

def test_debate_detail_loads(client, sample_debate):
    """Debate detail page loads for a public debate."""
    response = client.get(f"/debate/{sample_debate.id}")
    assert response.status_code == 200


def test_create_debate_requires_login(client):
    """Creating a debate redirects unauthenticated users to login."""
    response = client.post("/debates/create", data={
        "title": "Test",
        "description": "Test description",
        "category": "general",
        "duration_days": 1,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_create_debate_logged_in(logged_in_client, app):
    """A logged-in user can create a debate."""
    response = logged_in_client.post("/debates/create", data={
        "title": "New Debate",
        "description": "A debate description.",
        "category": "general",
        "duration_days": "1",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        debate = Debate.query.filter_by(title="New Debate").first()
        assert debate is not None


def test_voting_requires_login(client, sample_debate):
    """Voting redirects unauthenticated users to login."""
    response = client.post(f"/debates/{sample_debate.id}/vote", data={
        "vote_type": "agree",
    }, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_cast_vote(logged_in_client, sample_debate, app):
    """A logged-in user can cast a vote on a debate."""
    response = logged_in_client.post(f"/debates/{sample_debate.id}/vote", data={
        "vote_type": "agree",
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    with app.app_context():
        debate = db.session.get(Debate, sample_debate.id)
        assert debate.agree_votes == 1


def test_same_vote_toggles_removal(logged_in_client, sample_debate):
    """Voting the same way twice removes the vote (toggle behaviour)."""
    logged_in_client.post(f"/debates/{sample_debate.id}/vote", data={"vote_type": "agree"})
    response = logged_in_client.post(f"/debates/{sample_debate.id}/vote", data={"vote_type": "agree"})
    data = response.get_json()
    assert data["success"] is True
    assert data["removed"] is True


def test_vote_on_closed_debate_rejected(logged_in_client, app, sample_user):
    """Voting on a closed debate returns an error."""
    with app.app_context():
        debate = Debate(
            title="Closed Debate",
            description="This debate has ended.",
            category="general",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            user_id=sample_user.id,
        )
        db.session.add(debate)
        db.session.commit()
        debate_id = debate.id

    response = logged_in_client.post(f"/debates/{debate_id}/vote", data={"vote_type": "agree"})
    data = response.get_json()
    assert "error" in data


# ── API tests ─────────────────────────────────────────────────────

def test_bookmark_adds_debate_to_saved_page(logged_in_client, sample_debate, app):
    """A bookmarked debate appears on the saved debates page."""
    response = logged_in_client.post(f"/debates/{sample_debate.id}/bookmark")
    assert response.status_code == 200
    data = response.get_json()
    assert data["bookmarked"] is True

    with app.app_context():
        bookmark = Bookmark.query.filter_by(debate_id=sample_debate.id).first()
        assert bookmark is not None

    saved_response = logged_in_client.get("/saved-debates")
    assert saved_response.status_code == 200
    assert b"Test Debate" in saved_response.data
    assert b"```html" not in saved_response.data


def test_api_debates_returns_json(client, sample_debate):
    """The debates API returns valid JSON with a debates list."""
    response = client.get("/api/debates")
    assert response.status_code == 200
    data = response.get_json()
    assert "debates" in data
    assert isinstance(data["debates"], list)


def test_api_debates_contains_sample(client, sample_debate):
    """The debates API includes the sample debate."""
    response = client.get("/api/debates")
    data = response.get_json()
    titles = [d["title"] for d in data["debates"]]
    assert "Test Debate" in titles


def test_api_trending_tags_counts_open_public_debates(client, app, sample_user):
    """Trending tags are ranked by open public debate count."""
    def add_debate(title, category, expires_delta, is_private=False, is_closed=False):
        debate = Debate(
            title=title,
            description=title,
            category=category,
            expires_at=datetime.now(timezone.utc) + expires_delta,
            user_id=sample_user.id,
            is_private=is_private,
            is_closed=is_closed,
        )
        db.session.add(debate)

    with app.app_context():
        for index in range(3):
            add_debate(f"Politics {index}", "politics", timedelta(days=1))
        for index in range(2):
            add_debate(f"Technology {index}", "technology", timedelta(days=1))
        add_debate("Food", "food", timedelta(days=1))
        add_debate("Work", "work", timedelta(days=1))
        add_debate("Ended education", "education", timedelta(days=-1))
        add_debate("Closed education", "education", timedelta(days=1), is_closed=True)
        add_debate("Private lifestyle", "lifestyle", timedelta(days=1), is_private=True)
        db.session.commit()

    response = client.get("/api/trending-tags")
    assert response.status_code == 200
    tags = response.get_json()["tags"]
    assert [tag["tag"] for tag in tags] == ["politics", "technology", "food", "work"]
    assert tags[0]["count"] == 3
    assert tags[0]["url"] == "/search?tag=politics"


def test_api_me_requires_login(client):
    """The /api/me endpoint requires authentication."""
    response = client.get("/api/me")
    assert response.status_code == 302


def test_api_notifications_requires_login(client):
    """The notifications API requires authentication."""
    response = client.get("/api/notifications")
    assert response.status_code == 302


def test_post_comment_requires_login(client, sample_debate):
    """Posting a comment redirects unauthenticated users to login."""
    response = client.post(f"/debates/{sample_debate.id}/comments", data={
        "content": "A test comment.",
    }, follow_redirects=False)
    assert response.status_code == 302


def test_post_comment_logged_in(logged_in_client, sample_debate, app):
    """A logged-in user can post a comment."""
    response = logged_in_client.post(f"/debates/{sample_debate.id}/comments", data={
        "content": "A test comment.",
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    with app.app_context():
        comment = Comment.query.filter_by(content="A test comment.").first()
        assert comment is not None
