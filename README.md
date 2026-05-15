# DebateHub — CITS3403 Group Project

## Description

DebateHub is a web application where users create and participate in binary (Agree/Disagree) debates. Users post a debate prompt, set a duration, and the community votes. Vote distribution is hidden while the debate is live and revealed on expiry, when a winner is declared. Users earn reputation points for creating debates, voting, and commenting. A leaderboard ranks users by reputation, and a social system allows users to follow each other and track friend activity.

## Team

| UWA ID   | Name               | GitHub Username |
|----------|--------------------|-----------------|
| 24295598 | Rivin Sharma       | rivinsharma     |
| 24463533 | Alvin Gwatimba     | top-zizu        |
| 23833948 | Charlie Griffiths  | Chardgr         |
| 23724721 | Jamie Taylor       | Jamie23724721   |

## Launching the Application

### Prerequisites
- Python 3.10 or higher
- Git

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/top-zizu/CITS-3403-Project.git
   cd CITS-3403-Project
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate.bat        # Windows
   source venv/bin/activate         # macOS/Linux
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following:
   ```
   SECRET_KEY=your-secret-key-here
   ```

5. Initialise the database:
   ```
   flask db upgrade
   ```

6. (Optional) Seed the database with sample debates and users:
   ```
   python seed_debates.py
   ```

7. Run the application:
   ```
   flask run
   ```

8. Open your browser and navigate to `http://127.0.0.1:5000`

## Running the Tests

### Unit Tests

Ensure the virtual environment is active, then run:
```
python -m pytest tests/test_models.py tests/test_routes.py -v
```

### Selenium Tests

Ensure the Flask server is running (`flask run`) in a separate terminal, then run:
```
python -m pytest tests/test_selenium.py -v
```
