from datetime import datetime, timedelta, timezone

from app import app
from models import db, Debate, User


DEMO_USER = {
    "username": "demo_debater",
    "email": "demo@example.com",
    "password": "password123",
}


DEMO_DEBATES = [
    {
        "title": "Universal basic income should be implemented globally",
        "description": "Should every adult receive a guaranteed income from the government regardless of employment status?",
        "category": "politics",
        "duration_hours": 12,
        "agree_votes": 723,
        "disagree_votes": 556,
    },
    {
        "title": "Artificial Intelligence will create more jobs than it destroys",
        "description": "Will AI ultimately expand employment opportunities, or will automation permanently remove more jobs than it creates?",
        "category": "technology",
        "duration_hours": 18,
        "agree_votes": 445,
        "disagree_votes": 678,
    },
    {
        "title": "Climate change is the most pressing issue of our time",
        "description": "Should climate change be treated as the highest priority global challenge?",
        "category": "environment",
        "duration_days": 1,
        "agree_votes": 892,
        "disagree_votes": 234,
    },
    {
        "title": "Social media does more harm than good for society",
        "description": "Do the social costs of social media outweigh its benefits for communication and community?",
        "category": "lifestyle",
        "duration_days": 2,
        "agree_votes": 612,
        "disagree_votes": 389,
    },
    {
        "title": "Remote work is better than working in an office",
        "description": "Does remote work produce better outcomes for workers and organisations than office-based work?",
        "category": "work",
        "duration_days": 3,
        "agree_votes": 801,
        "disagree_votes": 420,
    },
    {
        "title": "Pineapple belongs on pizza",
        "description": "Is pineapple a valid and delicious pizza topping, or a culinary mistake?",
        "category": "food",
        "duration_hours": 6,
        "agree_votes": 334,
        "disagree_votes": 891,
    },
]


DEMO_SOCIAL_USERS = [
    {
        "username": "logicqueen",
        "email": "logicqueen@example.com",
        "bio": "Loves structured arguments and policy debates.",
    },
    {
        "username": "argumentking",
        "email": "argumentking@example.com",
        "bio": "Here for spicy claims and calm evidence.",
    },
    {
        "username": "voiceofreason",
        "email": "voiceofreason@example.com",
        "bio": "Usually looking for the middle ground.",
    },
    {
        "username": "contrarymary",
        "email": "contrarymary@example.com",
        "bio": "Professional devil's advocate.",
    },
    {
        "username": "mindchanger",
        "email": "mindchanger@example.com",
        "bio": "Open to being convinced.",
    },
]


DEMO_FOLLOWING = [
    "logicqueen",
    "argumentking",
    "voiceofreason",
]


DEMO_FOLLOWERS = [
    "voiceofreason",
    "contrarymary",
    "mindchanger",
]


def get_or_create_demo_user():
    user = User.query.filter_by(username=DEMO_USER["username"]).first()
    if user:
        return user

    user = User(username=DEMO_USER["username"], email=DEMO_USER["email"])
    user.set_password(DEMO_USER["password"])
    db.session.add(user)
    db.session.commit()
    return user


def get_or_create_social_user(user_data):
    user = User.query.filter_by(username=user_data["username"]).first()
    if user:
        if not user.bio:
            user.bio = user_data["bio"]
        return user

    user = User(
        username=user_data["username"],
        email=user_data["email"],
        bio=user_data["bio"],
    )
    user.set_password("password123")
    db.session.add(user)
    return user


def ensure_follow(follower, followed):
    if follower.id == followed.id:
        return False
    if follower.following.filter(User.id == followed.id).first():
        return False
    follower.following.append(followed)
    return True


def seed_social_graph():
    demo_user = get_or_create_demo_user()
    users_by_username = {}

    for user_data in DEMO_SOCIAL_USERS:
        user = get_or_create_social_user(user_data)
        users_by_username[user.username] = user

    db.session.flush()

    created_links = 0

    for username in DEMO_FOLLOWING:
        created_links += int(ensure_follow(demo_user, users_by_username[username]))

    for username in DEMO_FOLLOWERS:
        created_links += int(ensure_follow(users_by_username[username], demo_user))

    db.session.commit()
    print(f"Social seed complete: {len(users_by_username)} demo users ready, {created_links} follow links created.")


def seed_debates():
    demo_user = get_or_create_demo_user()
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0

    for item in DEMO_DEBATES:
        existing = Debate.query.filter_by(title=item["title"]).first()
        if existing:
            skipped += 1
            continue

        duration = timedelta(
            days=item.get("duration_days", 0),
            hours=item.get("duration_hours", 0),
        )

        debate = Debate(
            title=item["title"],
            description=item["description"],
            category=item["category"],
            expires_at=now + duration,
            agree_votes=item["agree_votes"],
            disagree_votes=item["disagree_votes"],
            user_id=demo_user.id,
        )
        db.session.add(debate)
        created += 1

    db.session.commit()
    print(f"Seed complete: {created} debates created, {skipped} already existed.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_debates()
        seed_social_graph()
