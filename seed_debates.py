from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app import app
from models import db, Debate, User, Comment, Vote, CommentLike

CURRENT_ALEMBIC_HEAD = "8b8a7c4d2f1e"


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
        "author": "argumentking",
        "duration_hours": 12,
        "agree_votes": 723,
        "disagree_votes": 556,
    },
    {
        "title": "Artificial Intelligence will create more jobs than it destroys",
        "description": "Will AI ultimately expand employment opportunities, or will automation permanently remove more jobs than it creates?",
        "category": "technology",
        "author": "logicqueen",
        "duration_hours": 18,
        "agree_votes": 445,
        "disagree_votes": 678,
    },
    {
        "title": "Climate change is the most pressing issue of our time",
        "description": "Should climate change be treated as the highest priority global challenge?",
        "category": "environment",
        "author": "voiceofreason",
        "duration_days": 1,
        "agree_votes": 892,
        "disagree_votes": 234,
    },
    {
        "title": "Social media does more harm than good for society",
        "description": "Do the social costs of social media outweigh its benefits for communication and community?",
        "category": "lifestyle",
        "author": "mindchanger",
        "duration_days": 2,
        "agree_votes": 612,
        "disagree_votes": 389,
    },
    {
        "title": "Remote work is better than working in an office",
        "description": "Does remote work produce better outcomes for workers and organisations than office-based work?",
        "category": "work",
        "author": "demo_debater",
        "duration_days": 3,
        "agree_votes": 801,
        "disagree_votes": 420,
    },
    {
        "title": "Pineapple belongs on pizza",
        "description": "Is pineapple a valid and delicious pizza topping, or a culinary mistake?",
        "category": "food",
        "author": "contrarymary",
        "duration_hours": 6,
        "agree_votes": 334,
        "disagree_votes": 891,
    },
    {
        "title": "Schools should ban smartphones during class",
        "description": "Would phone-free classrooms improve learning and attention, or would bans create more problems than they solve?",
        "category": "education",
        "author": "consensusbuilder",
        "expired_days_ago": 2,
        "agree_votes": 742,
        "disagree_votes": 418,
        "winner": "agree",
        "is_closed": True,
    },
    {
        "title": "Nuclear energy should be central to climate policy",
        "description": "Should governments prioritise nuclear power as a major clean energy source?",
        "category": "environment",
        "author": "perspectiveseeker",
        "expired_days_ago": 5,
        "agree_votes": 528,
        "disagree_votes": 611,
        "winner": "disagree",
        "is_closed": True,
    },
]


def ensure_schema_compatibility():
    comment_columns = {
        column["name"]
        for column in db.session.execute(text("PRAGMA table_info(comment)")).mappings()
    }

    if "stance" not in comment_columns:
        db.session.execute(
            text("ALTER TABLE comment ADD COLUMN stance VARCHAR(20) NOT NULL DEFAULT 'neutral'")
        )

    db.session.execute(text("""
        UPDATE comment
        SET stance = CASE (
            SELECT vote.vote_type
            FROM vote
            WHERE vote.user_id = comment.user_id
              AND vote.debate_id = comment.debate_id
            LIMIT 1
        )
            WHEN 'agree' THEN 'blue'
            WHEN 'disagree' THEN 'red'
            ELSE COALESCE(stance, 'neutral')
        END
    """))

    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    """))
    existing_revision = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar()
    if existing_revision != CURRENT_ALEMBIC_HEAD:
        db.session.execute(text("DELETE FROM alembic_version"))
        db.session.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": CURRENT_ALEMBIC_HEAD},
        )

    db.session.commit()


DEMO_SOCIAL_USERS = [
    {
        "username": "consensusbuilder",
        "email": "consensusbuilder@example.com",
        "bio": "Usually spots where the room is heading before the poll closes.",
    },
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
    {
        "username": "perspectiveseeker",
        "email": "perspectiveseeker@example.com",
        "bio": "Collects thoughtful edge cases and better questions.",
    },
]


DEMO_FOLLOWING = [
    "consensusbuilder",
    "logicqueen",
    "argumentking",
    "voiceofreason",
    "perspectiveseeker",
]


DEMO_FOLLOWERS = [
    "voiceofreason",
    "contrarymary",
    "mindchanger",
    "consensusbuilder",
]


DEMO_LEADERBOARD_TARGETS = {
    "argumentking": {"points": 1523, "conformity": 28, "won": 8, "lost": 20},
    "consensusbuilder": {"points": 1345, "conformity": 89, "won": 23, "lost": 3},
    "demo_debater": {"points": 1247, "conformity": 67, "won": 16, "lost": 8},
    "voiceofreason": {"points": 1156, "conformity": 73, "won": 18, "lost": 7},
    "logicqueen": {"points": 1089, "conformity": 64, "won": 15, "lost": 9},
    "contrarymary": {"points": 987, "conformity": 15, "won": 4, "lost": 22},
    "mindchanger": {"points": 876, "conformity": 45, "won": 11, "lost": 13},
    "perspectiveseeker": {"points": 765, "conformity": 51, "won": 12, "lost": 12},
}


DEMO_ACTIVITY_DEBATES = [
    {
        "title": "Universities should make attendance optional",
        "description": "Should students be trusted to manage attendance if assessments prove mastery?",
        "category": "education",
        "author": "logicqueen",
        "duration_hours": 36,
        "agree": ["argumentking", "contrarymary", "mindchanger", "perspectiveseeker"],
        "disagree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason"],
        "comments": ["logicqueen", "argumentking", "voiceofreason", "mindchanger"],
    },
    {
        "title": "Public transport should be free in major cities",
        "description": "Would free public transport reduce congestion enough to justify the cost?",
        "category": "politics",
        "author": "consensusbuilder",
        "duration_hours": 28,
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason", "perspectiveseeker"],
        "disagree": ["argumentking", "contrarymary", "mindchanger"],
        "comments": ["consensusbuilder", "contrarymary", "perspectiveseeker", "demo_debater"],
    },
    {
        "title": "Four-day work weeks should become standard",
        "description": "Can shorter weeks improve productivity and wellbeing without hurting output?",
        "category": "work",
        "author": "voiceofreason",
        "duration_hours": 44,
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "mindchanger", "voiceofreason"],
        "disagree": ["argumentking", "contrarymary", "perspectiveseeker"],
        "comments": ["voiceofreason", "argumentking", "logicqueen", "mindchanger"],
    },
    {
        "title": "Streaming services are worse than cable became",
        "description": "Have too many subscriptions recreated the problems streaming originally solved?",
        "category": "entertainment",
        "author": "mindchanger",
        "duration_hours": 20,
        "agree": ["argumentking", "contrarymary", "demo_debater", "mindchanger", "perspectiveseeker"],
        "disagree": ["consensusbuilder", "logicqueen", "voiceofreason"],
        "comments": ["mindchanger", "perspectiveseeker", "consensusbuilder", "contrarymary"],
    },
    {
        "title": "Cities should prioritise bike lanes over parking",
        "description": "Should scarce street space move people rather than store private cars?",
        "category": "lifestyle",
        "author": "perspectiveseeker",
        "duration_hours": 52,
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason", "perspectiveseeker"],
        "disagree": ["argumentking", "contrarymary", "mindchanger"],
        "comments": ["perspectiveseeker", "voiceofreason", "argumentking", "logicqueen"],
    },
    {
        "title": "Esports should be treated like traditional sports",
        "description": "Do skill, training, spectatorship, and competition make esports sports?",
        "category": "sports",
        "author": "argumentking",
        "duration_hours": 18,
        "agree": ["argumentking", "demo_debater", "mindchanger", "perspectiveseeker"],
        "disagree": ["consensusbuilder", "contrarymary", "logicqueen", "voiceofreason"],
        "comments": ["argumentking", "contrarymary", "demo_debater", "voiceofreason"],
    },
    {
        "title": "Restaurants should ban split bills for large groups",
        "description": "Is simplicity for staff worth the inconvenience for diners?",
        "category": "food",
        "author": "contrarymary",
        "duration_hours": 60,
        "agree": ["argumentking", "contrarymary", "logicqueen"],
        "disagree": ["consensusbuilder", "demo_debater", "mindchanger", "voiceofreason", "perspectiveseeker"],
        "comments": ["contrarymary", "consensusbuilder", "mindchanger", "perspectiveseeker"],
    },
    {
        "title": "Pet owners should need a licence for high-maintenance animals",
        "description": "Would licensing improve welfare without unfairly punishing responsible owners?",
        "category": "animals",
        "author": "demo_debater",
        "duration_hours": 72,
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason"],
        "disagree": ["argumentking", "contrarymary", "mindchanger", "perspectiveseeker"],
        "comments": ["demo_debater", "logicqueen", "contrarymary", "voiceofreason"],
    },
    {
        "title": "Open-source AI models are safer than closed models",
        "description": "Does transparency help safety more than it helps misuse?",
        "category": "technology",
        "author": "logicqueen",
        "expired_days_ago": 1,
        "winner": "disagree",
        "agree": ["argumentking", "contrarymary", "mindchanger"],
        "disagree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason", "perspectiveseeker"],
        "comments": ["logicqueen", "argumentking", "consensusbuilder", "perspectiveseeker"],
    },
    {
        "title": "Compulsory voting improves democracy",
        "description": "Does requiring everyone to vote create better representation?",
        "category": "politics",
        "author": "voiceofreason",
        "expired_days_ago": 3,
        "winner": "agree",
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason", "perspectiveseeker"],
        "disagree": ["argumentking", "contrarymary", "mindchanger"],
        "comments": ["voiceofreason", "contrarymary", "demo_debater", "logicqueen"],
    },
    {
        "title": "Kids should learn coding before high school",
        "description": "Should programming become a core early-years literacy?",
        "category": "education",
        "author": "consensusbuilder",
        "expired_days_ago": 4,
        "winner": "agree",
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "mindchanger", "voiceofreason"],
        "disagree": ["argumentking", "contrarymary", "perspectiveseeker"],
        "comments": ["consensusbuilder", "mindchanger", "argumentking", "voiceofreason"],
    },
    {
        "title": "Reality TV has cultural value",
        "description": "Can reality television teach us something meaningful about society?",
        "category": "entertainment",
        "author": "mindchanger",
        "expired_days_ago": 6,
        "winner": "disagree",
        "agree": ["argumentking", "mindchanger", "perspectiveseeker"],
        "disagree": ["consensusbuilder", "contrarymary", "demo_debater", "logicqueen", "voiceofreason"],
        "comments": ["mindchanger", "perspectiveseeker", "contrarymary", "demo_debater"],
    },
    {
        "title": "Professional athletes are overpaid",
        "description": "Are elite sports salaries justified by revenue and scarcity?",
        "category": "sports",
        "author": "argumentking",
        "expired_days_ago": 8,
        "winner": "disagree",
        "agree": ["contrarymary", "mindchanger"],
        "disagree": ["argumentking", "consensusbuilder", "demo_debater", "logicqueen", "voiceofreason", "perspectiveseeker"],
        "comments": ["argumentking", "voiceofreason", "contrarymary", "consensusbuilder"],
    },
    {
        "title": "Meal kits are worth the premium",
        "description": "Do convenience and reduced waste justify higher per-meal costs?",
        "category": "food",
        "author": "perspectiveseeker",
        "expired_days_ago": 10,
        "winner": "agree",
        "agree": ["consensusbuilder", "demo_debater", "mindchanger", "perspectiveseeker", "voiceofreason"],
        "disagree": ["argumentking", "contrarymary", "logicqueen"],
        "comments": ["perspectiveseeker", "logicqueen", "mindchanger", "argumentking"],
    },
    {
        "title": "Office pets improve workplace culture",
        "description": "Are animals at work a morale boost or a distraction and access problem?",
        "category": "animals",
        "author": "demo_debater",
        "expired_days_ago": 12,
        "winner": "agree",
        "agree": ["consensusbuilder", "demo_debater", "mindchanger", "voiceofreason"],
        "disagree": ["argumentking", "contrarymary", "logicqueen", "perspectiveseeker"],
        "comments": ["demo_debater", "contrarymary", "voiceofreason", "consensusbuilder"],
    },
    {
        "title": "Personal carbon budgets are fairer than carbon taxes",
        "description": "Would individual allowances target emissions more justly than broad price signals?",
        "category": "environment",
        "author": "logicqueen",
        "expired_days_ago": 14,
        "winner": "agree",
        "agree": ["consensusbuilder", "demo_debater", "logicqueen", "voiceofreason"],
        "disagree": ["argumentking", "contrarymary", "mindchanger", "perspectiveseeker"],
        "comments": ["logicqueen", "perspectiveseeker", "argumentking", "voiceofreason"],
    },
]


DEMO_COMMENT_LINES = {
    "argumentking": "The headline sounds tidy, but the trade-offs underneath it are doing all the work.",
    "consensusbuilder": "Most people will land on this once the practical details are separated from the slogan.",
    "contrarymary": "The popular answer misses the incentives. People behave differently when the policy is real.",
    "demo_debater": "I can see both sides, but the strongest argument is the one with fewer hidden costs.",
    "logicqueen": "The evidence points one way, but only if we define the outcome we actually care about.",
    "mindchanger": "I started on the other side of this, but the better examples nudged me across.",
    "perspectiveseeker": "The edge cases are doing more work here than the average case.",
    "voiceofreason": "This probably needs a middle path rather than a clean yes or no.",
}


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


def get_seed_users():
    users = {DEMO_USER["username"]: get_or_create_demo_user()}
    for user_data in DEMO_SOCIAL_USERS:
        users[user_data["username"]] = get_or_create_social_user(user_data)
    db.session.flush()
    return users


def ensure_follow(follower, followed):
    if follower.id == followed.id:
        return False
    if follower.following.filter(User.id == followed.id).first():
        return False
    follower.following.append(followed)
    return True


def seed_social_graph():
    users_by_username = get_seed_users()
    demo_user = users_by_username[DEMO_USER["username"]]

    created_links = 0

    for username in DEMO_FOLLOWING:
        if username in users_by_username:
            created_links += int(ensure_follow(demo_user, users_by_username[username]))

    for username in DEMO_FOLLOWERS:
        if username in users_by_username:
            created_links += int(ensure_follow(users_by_username[username], demo_user))

    db.session.commit()
    print(f"Social seed complete: {len(users_by_username) - 1} demo users ready, {created_links} follow links created.")


def seed_debates():
    users = get_seed_users()
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0
    reassigned = 0

    for item in DEMO_DEBATES:
        author = users.get(item.get("author"), users[DEMO_USER["username"]])
        existing = Debate.query.filter_by(title=item["title"]).first()
        if existing:
            if existing.user_id != author.id:
                existing.user_id = author.id
                reassigned += 1
            skipped += 1
            continue

        if "expired_days_ago" in item or "expired_hours_ago" in item:
            duration = timedelta(
                days=item.get("expired_days_ago", 0),
                hours=item.get("expired_hours_ago", 0),
            )
            expires_at = now - duration
        else:
            duration = timedelta(
                days=item.get("duration_days", 0),
                hours=item.get("duration_hours", 0),
            )
            expires_at = now + duration

        debate = Debate(
            title=item["title"],
            description=item["description"],
            category=item["category"],
            expires_at=expires_at,
            agree_votes=item["agree_votes"],
            disagree_votes=item["disagree_votes"],
            winner=item.get("winner"),
            is_closed=item.get("is_closed", False),
            user_id=author.id,
        )
        db.session.add(debate)
        created += 1

    db.session.commit()
    print(f"Seed complete: {created} debates created, {skipped} already existed, {reassigned} reassigned.")


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
    {
        "debate_title": "Schools should ban smartphones during class",
        "comments": [
            {
                "username": "mindchanger",
                "content": "The closed result makes sense to me. A classroom is one of the few places where sustained attention should be protected by default.",
                "vote": "agree",
                "likes": ["demo_debater", "logicqueen", "argumentking", "voiceofreason", "contrarymary"],
                "replies": [
                    {
                        "username": "logicqueen",
                        "content": "I agree with the principle, but a blanket ban needs careful exceptions for accessibility, medical alerts, and students with caring responsibilities.",
                        "vote": "agree",
                        "likes": ["demo_debater", "argumentking", "voiceofreason", "contrarymary", "mindchanger"],
                    },
                    {
                        "username": "voiceofreason",
                        "content": "The strongest counterpoint is enforcement. If teachers spend ten minutes policing phones every lesson, the policy can eat the attention it was meant to save.",
                        "vote": None,
                        "likes": ["demo_debater", "logicqueen", "argumentking", "contrarymary"],
                    },
                    {
                        "username": "argumentking",
                        "content": "Teaching responsible use is better than pretending phones do not exist. Students need self-regulation skills before they leave school.",
                        "vote": "disagree",
                        "likes": ["demo_debater", "logicqueen", "voiceofreason"],
                    },
                    {
                        "username": "contrarymary",
                        "content": "Bans usually hit responsible students hardest while the determined rule-breakers just get better at hiding it.",
                        "vote": "disagree",
                        "likes": ["logicqueen", "voiceofreason"],
                    },
                ],
            },
            {
                "username": "argumentking",
                "content": "The vote went the wrong way. Schools should model good technology habits instead of building a tiny prohibition system.",
                "vote": "disagree",
                "likes": ["demo_debater", "voiceofreason", "contrarymary", "mindchanger"],
                "replies": [
                    {
                        "username": "logicqueen",
                        "content": "Modelling habits matters, but younger students are not choosing on equal footing against apps designed to pull attention.",
                        "vote": "agree",
                        "likes": ["demo_debater", "voiceofreason", "mindchanger"],
                    },
                    {
                        "username": "voiceofreason",
                        "content": "Maybe the distinction should be phones away during instruction, available during breaks, with clear exceptions.",
                        "vote": None,
                        "likes": ["demo_debater", "logicqueen", "contrarymary"],
                    },
                ],
            },
            {
                "username": "voiceofreason",
                "content": "I would rather see a structured phone policy than a pure ban. The goal is attention, not punishment.",
                "vote": None,
                "likes": ["logicqueen", "argumentking", "mindchanger"],
            },
            {
                "username": "logicqueen",
                "content": "The evidence from schools that use phone lockers is pretty persuasive: fewer disruptions, more face-to-face interaction, and calmer breaks.",
                "vote": "agree",
                "likes": ["demo_debater", "voiceofreason", "mindchanger"],
            },
        ],
    },
    {
        "debate_title": "Nuclear energy should be central to climate policy",
        "comments": [
            {"username": "contrarymary", "content": "The result reflects the practical issue: nuclear is slow and expensive compared with renewables plus storage.", "vote": "disagree", "likes": ["argumentking", "voiceofreason", "mindchanger"]},
            {"username": "logicqueen", "content": "I still think the debate underrates firm low-carbon power. Grid reliability matters when the weather does not cooperate.", "vote": "agree", "likes": ["demo_debater", "voiceofreason"]},
            {"username": "voiceofreason", "content": "The answer probably depends on country context: existing expertise, regulation, geography, and public trust.", "vote": None, "likes": ["logicqueen", "argumentking"]},
        ],
    },
]


def seed_comments():
    social_users = get_seed_users()

    created_comments = 0
    created_votes = 0
    created_likes = 0
    skipped = 0

    def ensure_vote(user, debate, vote_type):
        nonlocal created_votes
        if not vote_type:
            return

        existing_vote = Vote.query.filter_by(
            user_id=user.id, debate_id=debate.id
        ).first()
        if existing_vote:
            return

        vote = Vote(
            user_id=user.id,
            debate_id=debate.id,
            vote_type=vote_type,
        )
        if vote_type == "agree":
            debate.agree_votes += 1
        else:
            debate.disagree_votes += 1
        db.session.add(vote)
        created_votes += 1

    def stance_for(user, debate):
        vote = Vote.query.filter_by(user_id=user.id, debate_id=debate.id).first()
        if not vote:
            return "neutral"
        return "blue" if vote.vote_type == "agree" else "red"

    def ensure_comment(item, debate, parent=None):
        nonlocal created_comments, skipped
        user = social_users.get(item["username"])
        if not user:
            return None

        ensure_vote(user, debate, item.get("vote"))

        existing = Comment.query.filter_by(
            user_id=user.id,
            debate_id=debate.id,
            content=item["content"],
            parent_comment_id=parent.id if parent else None,
        ).first()
        if existing:
            skipped += 1
            return existing

        comment = Comment(
            user_id=user.id,
            debate_id=debate.id,
            content=item["content"],
            stance=stance_for(user, debate),
            parent_comment_id=parent.id if parent else None,
        )
        db.session.add(comment)
        db.session.flush()
        created_comments += 1
        return comment

    def ensure_likes(comment, like_usernames):
        nonlocal created_likes
        if not comment:
            return

        for username in like_usernames:
            user = social_users.get(username)
            if not user:
                continue

            existing_like = CommentLike.query.filter_by(
                user_id=user.id,
                comment_id=comment.id,
            ).first()
            if existing_like:
                continue

            db.session.add(CommentLike(user_id=user.id, comment_id=comment.id))
            created_likes += 1

    for debate_data in DEMO_COMMENTS:
        debate = Debate.query.filter_by(title=debate_data["debate_title"]).first()
        if not debate:
            print(f"  Debate not found, skipping: {debate_data['debate_title']}")
            continue

        for item in debate_data["comments"]:
            comment = ensure_comment(item, debate)
            ensure_likes(comment, item.get("likes", []))

            if not comment:
                continue

            for reply_data in item.get("replies", []):
                reply = ensure_comment(reply_data, debate, parent=comment)
                ensure_likes(reply, reply_data.get("likes", []))

    db.session.commit()
    print(
        "Comment seed complete: "
        f"{created_comments} comments created, "
        f"{created_votes} votes created, "
        f"{created_likes} likes created, "
        f"{skipped} skipped."
    )


def seed_leaderboard_activity():
    users = get_seed_users()
    now = datetime.now(timezone.utc)
    created_debates = 0
    created_votes = 0
    created_comments = 0
    created_likes = 0

    def ensure_activity_vote(user, debate, vote_type):
        nonlocal created_votes
        if vote_type not in {"agree", "disagree"}:
            return

        existing_vote = Vote.query.filter_by(
            user_id=user.id,
            debate_id=debate.id,
        ).first()
        if existing_vote:
            existing_vote.vote_type = vote_type
            return

        db.session.add(Vote(
            user_id=user.id,
            debate_id=debate.id,
            vote_type=vote_type,
        ))
        created_votes += 1

    def stance_for(user, debate):
        vote = Vote.query.filter_by(user_id=user.id, debate_id=debate.id).first()
        if not vote:
            return "neutral"
        return "blue" if vote.vote_type == "agree" else "red"

    def ensure_activity_comment(username, debate):
        nonlocal created_comments, created_likes
        user = users.get(username)
        if not user:
            return

        content = f"{DEMO_COMMENT_LINES[username]} ({debate.title})"
        comment = Comment.query.filter_by(
            user_id=user.id,
            debate_id=debate.id,
            content=content,
            parent_comment_id=None,
        ).first()

        if not comment:
            comment = Comment(
                user_id=user.id,
                debate_id=debate.id,
                content=content,
                stance=stance_for(user, debate),
                parent_comment_id=None,
            )
            db.session.add(comment)
            db.session.flush()
            created_comments += 1
        elif not comment.stance:
            comment.stance = stance_for(user, debate)

        liker_names = [
            name for name in DEMO_LEADERBOARD_TARGETS
            if name != username
        ][:3]
        for liker_name in liker_names:
            liker = users.get(liker_name)
            if not liker:
                continue
            existing_like = CommentLike.query.filter_by(
                user_id=liker.id,
                comment_id=comment.id,
            ).first()
            if existing_like:
                continue
            db.session.add(CommentLike(user_id=liker.id, comment_id=comment.id))
            created_likes += 1

    for item in DEMO_ACTIVITY_DEBATES:
        author = users[item["author"]]
        debate = Debate.query.filter_by(title=item["title"]).first()

        if debate:
            debate.user_id = author.id
            debate.description = item["description"]
            debate.category = item["category"]
        else:
            if "expired_days_ago" in item:
                expires_at = now - timedelta(days=item["expired_days_ago"])
            else:
                expires_at = now + timedelta(hours=item.get("duration_hours", 24))

            debate = Debate(
                title=item["title"],
                description=item["description"],
                category=item["category"],
                expires_at=expires_at,
                user_id=author.id,
                agree_votes=0,
                disagree_votes=0,
            )
            db.session.add(debate)
            db.session.flush()
            created_debates += 1

        if "expired_days_ago" in item:
            debate.expires_at = now - timedelta(days=item["expired_days_ago"])
            debate.is_closed = True
            debate.winner = item["winner"]
        else:
            debate.expires_at = now + timedelta(hours=item.get("duration_hours", 24))
            debate.is_closed = False
            debate.winner = None

        for username in item.get("agree", []):
            ensure_activity_vote(users[username], debate, "agree")
        for username in item.get("disagree", []):
            ensure_activity_vote(users[username], debate, "disagree")

        db.session.flush()
        debate.agree_votes = Vote.query.filter_by(debate_id=debate.id, vote_type="agree").count()
        debate.disagree_votes = Vote.query.filter_by(debate_id=debate.id, vote_type="disagree").count()

        for username in item.get("comments", []):
            ensure_activity_comment(username, debate)

    db.session.commit()
    print(
        "Leaderboard activity seed complete: "
        f"{created_debates} debates created, "
        f"{created_votes} votes created, "
        f"{created_comments} comments created, "
        f"{created_likes} likes created."
    )


def seed_leaderboard_scores():
    users = get_seed_users()

    for username, targets in DEMO_LEADERBOARD_TARGETS.items():
        user = users.get(username)
        if not user:
            continue

        user.reputation_score = max(user.reputation_score or 0, targets["points"])
        user.conformity_score = targets["conformity"]
        user.debates_won = max(user.debates_won or 0, targets["won"])
        user.debates_lost = max(user.debates_lost or 0, targets["lost"])

    db.session.commit()
    print(f"Leaderboard score seed complete: {len(DEMO_LEADERBOARD_TARGETS)} users balanced.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_schema_compatibility()
        seed_social_graph()
        seed_debates()
        seed_comments()
        seed_leaderboard_activity()
        seed_leaderboard_scores()
