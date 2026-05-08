import sqlite3
import os

# We will store the database inside the 'instance' folder
DB_PATH = "instance/quiz_app.db"

def get_db_connection():
    # Ensure the instance folder exists before trying to connect
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Existing Quizzes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            difficulty TEXT,
            questions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Users Table for Accounts and Game Stats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            rank TEXT DEFAULT 'Academy Student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- MIGRATION: Ensure 'rank' column exists for older databases ---
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'rank' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN rank TEXT DEFAULT 'Academy Student'")

    # 3. NEW: User Results Table for Leaderboard and History
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

# --- EXISTING QUIZ FUNCTIONS ---

def save_quiz(topic, difficulty, questions_json):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quizzes (topic, difficulty, questions) VALUES (?, ?, ?)",
        (topic, difficulty, questions_json)
    )
    conn.commit()
    conn.close()

# --- NEW USER ACCOUNT FUNCTIONS ---

def create_user(username, password_hash):
    """Saves a new user to the database. Returns False if username is taken."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True # Account created successfully
    except sqlite3.IntegrityError:
        return False # The username already exists
    finally:
        conn.close()

def get_user_by_username(username):
    """Fetches user data for logging in."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_stats(user_id, score, xp, streak, rank):
    """Saves the player's progress so they don't lose their rank."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET score = ?, xp = ?, streak = ?, rank = ? WHERE id = ?",
        (score, xp, streak, rank, user_id)
    )
    conn.commit()
    conn.close()

def save_quiz_result(user_id, topic, score, total):
    """Records an individual quiz attempt."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_results (user_id, topic, score, total_questions) VALUES (?, ?, ?, ?)",
        (user_id, topic, score, total)
    )
    conn.commit()
    conn.close()

def get_leaderboard():
    """Fetches the top 10 users based on XP."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, xp, rank, streak 
        FROM users 
        ORDER BY xp DESC 
        LIMIT 10
    """)
    top_users = cursor.fetchall()
    conn.close()
    return [dict(user) for user in top_users]

def get_user_top_scores(user_id):
    """Fetches the top 5 scores for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT topic, score, total_questions, completed_at 
        FROM user_results 
        WHERE user_id = ? 
        ORDER BY score DESC 
        LIMIT 5
    """, (user_id,))
    scores = cursor.fetchall()
    conn.close()
    return [dict(s) for s in scores]

def get_user_recent_activity(user_id):
    """Fetches the last 5 quiz attempts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT topic, score, total_questions, completed_at 
        FROM user_results 
        WHERE user_id = ? 
        ORDER BY completed_at DESC 
        LIMIT 5
    """, (user_id,))
    activity = cursor.fetchall()
    conn.close()
    return [dict(a) for a in activity]

def get_user_mastery(user_id):
    """Calculates mastery (average score percentage) per topic with a 100% cap."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT topic, 
               COUNT(*) as attempts, 
               MIN(100.0, ROUND(AVG(CAST(score AS FLOAT) / total_questions) * 100, 1)) as mastery_score
        FROM user_results 
        WHERE user_id = ? 
        GROUP BY topic 
        ORDER BY mastery_score DESC
    """, (user_id,))
    mastery = cursor.fetchall()
    conn.close()
    return [dict(m) for m in mastery]