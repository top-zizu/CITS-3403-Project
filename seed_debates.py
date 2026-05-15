from datetime import datetime, timedelta, timezone

from app import app
from models import db, Debate, User, Comment, Vote


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


DEMO_COMMENTS = [
    {
        "debate_title": "Universal basic income should be implemented globally",
        "comments": [
            {"username": "logicqueen",    "content": "UBI addresses structural unemployment caused by automation. The Finland pilot showed promising results.", "vote": "agree"},
            {"username": "argumentking", "content": "The cost is prohibitive. Where does the funding come from without crushing tax increases on the middle class?", "vote": "disagree"},
            {"username": "voiceofreason","content": "Implementation details matter more than the concept itself. A badly designed UBI could be worse than nothing.", "vote": None},
            {"username": "contrarymary", "content": "Unconditional income removes the incentive to contribute. Society functions on reciprocal effort.", "vote": "disagree"},
            {"username": "mindchanger",  "content": "I was sceptical but the data from pilot programmes is genuinely compelling.", "vote": "agree"},
        ],
    },
    {
        "debate_title": "Artificial Intelligence will create more jobs than it destroys",
        "comments": [
            {"username": "logicqueen",    "content": "Every major technological shift has historically created more jobs than it eliminated. AI is no different.", "vote": "agree"},
            {"username": "argumentking", "content": "Previous shifts took decades. AI is moving at a pace that workers simply cannot retrain fast enough to match.", "vote": "disagree"},
            {"username": "contrarymary", "content": "The jobs AI creates require very different skills to the ones it destroys. That gap is the real problem.", "vote": "disagree"},
            {"username": "mindchanger",  "content": "New industries like AI safety, model auditing, and prompt engineering did not exist five years ago.", "vote": "agree"},
        ],
    },
    {
        "debate_title": "Climate change is the most pressing issue of our time",
        "comments": [
            {"username": "voiceofreason","content": "The scientific consensus is unambiguous. The question is purely about political will.", "vote": "agree"},
            {"username": "argumentking", "content": "Pandemics and nuclear proliferation are existential risks on a shorter timeline. Priority matters.", "vote": "disagree"},
            {"username": "logicqueen",    "content": "Climate change compounds every other crisis — food security, migration, conflict. It is the multiplier.", "vote": "agree"},
            {"username": "contrarymary", "content": "We have been told it is the most pressing issue for 30 years and emissions keep rising. The framing is not working.", "vote": "disagree"},
        ],
    },
    {
        "debate_title": "Social media does more harm than good for society",
        "comments": [
            {"username": "mindchanger",  "content": "The mental health data on teenagers is damning. We would not accept this from any other product.", "vote": "agree"},
            {"username": "logicqueen",    "content": "Social media connected activist movements and brought down authoritarian governments. That is not nothing.", "vote": "disagree"},
            {"username": "argumentking", "content": "Algorithmic amplification of outrage is a deliberate design choice, not a side effect. That is the problem.", "vote": "agree"},
            {"username": "voiceofreason","content": "The harm is real but so is the benefit. The issue is regulation, not the technology itself.", "vote": None},
        ],
    },
    {
        "debate_title": "Remote work is better than working in an office",
        "comments": [
            {"username": "contrarymary", "content": "Junior employees lose mentorship and osmotic learning. Remote work advantages those who are already established.", "vote": "disagree"},
            {"username": "mindchanger",  "content": "Two hours of commuting saved per day is two hours of life returned. That is not trivial.", "vote": "agree"},
            {"username": "logicqueen",    "content": "Productivity data is mixed and heavily dependent on role type. This is not a universal answer.", "vote": None},
            {"username": "argumentking", "content": "Collaboration suffers. The best ideas I have had came from a hallway conversation, not a scheduled Zoom.", "vote": "disagree"},
            {"username": "voiceofreason","content": "Hybrid is clearly the answer most people actually want, which suggests neither extreme is right.", "vote": "agree"},
        ],
    },
    {
        "debate_title": "Pineapple belongs on pizza",
        "comments": [
            {"username": "argumentking", "content": "Sweet and savoury is a legitimate flavour combination used in cuisines worldwide. The outrage is performative.", "vote": "agree"},
            {"username": "contrarymary", "content": "The moisture content ruins the base. This is not an opinion, it is food science.", "vote": "disagree"},
            {"username": "mindchanger",  "content": "I used to hate it. Then I tried a good Hawaiian with quality ham and proper mozzarella. Changed my mind.", "vote": "agree"},
            {"username": "voiceofreason","content": "Put whatever you want on your pizza. The gatekeeping is the embarrassing part.", "vote": "agree"},
            {"username": "logicqueen",    "content": "Texture contrast is a valid complaint. Pineapple releases water when heated and softens everything around it.", "vote": "disagree"},
        ],
    },
]


def seed_comments():
    social_users = {u["username"]: User.query.filter_by(username=u["username"]).first()
                    for u in DEMO_SOCIAL_USERS}

    created_comments = 0
    created_votes = 0
    skipped = 0

    for debate_data in DEMO_COMMENTS:
        debate = Debate.query.filter_by(title=debate_data["debate_title"]).first()
        if not debate:
            print(f"  Debate not found, skipping: {debate_data['debate_title']}")
            continue

        for item in debate_data["comments"]:
            user = social_users.get(item["username"])
            if not user:
                continue

            existing = Comment.query.filter_by(
                user_id=user.id,
                debate_id=debate.id,
                content=item["content"],
            ).first()
            if existing:
                skipped += 1
                continue

            if item["vote"]:
                existing_vote = Vote.query.filter_by(
                    user_id=user.id, debate_id=debate.id
                ).first()
                if not existing_vote:
                    vote = Vote(
                        user_id=user.id,
                        debate_id=debate.id,
                        vote_type=item["vote"],
                    )
                    if item["vote"] == "agree":
                        debate.agree_votes += 1
                    else:
                        debate.disagree_votes += 1
                    db.session.add(vote)
                    created_votes += 1

            comment = Comment(
                user_id=user.id,
                debate_id=debate.id,
                content=item["content"],
                parent_comment_id=None,
            )
            db.session.add(comment)
            created_comments += 1

    db.session.commit()
    print(f"Comment seed complete: {created_comments} comments created, {created_votes} votes created, {skipped} skipped.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_debates()
        seed_social_graph()
        seed_comments()
