import os
import json
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from .ai_service import generate_quiz
# Import our new database functions
from .database import save_quiz, create_user, get_user_by_username, update_user_stats

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf"}

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route("/")
def home():
    return render_template("index.html")

# --- NEW: ACCOUNT & STATS ROUTES ---

@main.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # Never save plain text passwords! Hash it first.
    hashed_password = generate_password_hash(password)

    if create_user(username, hashed_password):
        return jsonify({"message": "Account created successfully! You can now log in."})
    else:
        return jsonify({"error": "Username is already taken."}), 409

@main.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = get_user_by_username(username)

    # Verify the user exists AND the password matches the hashed version
    if user and check_password_hash(user["password_hash"], password):
        # Save a "cookie" in the session so the server remembers them
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        
        # Send their saved stats back to the frontend
        return jsonify({
            "message": "Login successful!",
            "username": user["username"],
            "score": user["score"],
            "xp": user["xp"],
            "streak": user["streak"]
        })
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@main.route("/api/logout", methods=["POST"])
def logout():
    session.clear() # Erase the user's session data
    return jsonify({"message": "Logged out successfully"})

@main.route("/dashboard")
def dashboard():
    # If the user is not logged in, they can't see the dashboard
    if "user_id" not in session:
        return render_template("index.html") # Redirect to home/login
    
    # We will pass the user's top scores to the template
    from .database import get_user_top_scores
    top_scores = get_user_top_scores(session["user_id"])
    
    return render_template("dashboard.html", top_scores=top_scores)

@main.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    from .database import get_leaderboard
    return jsonify(get_leaderboard())

@main.route("/api/user_extended_stats", methods=["GET"])
def user_extended_stats():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    from .database import get_user_by_username, get_user_recent_activity, get_user_mastery
    
    # We use username from session to get full user object
    user = get_user_by_username(session["username"])
    recent = get_user_recent_activity(user_id)
    mastery = get_user_mastery(user_id)
    
    return jsonify({
        "xp": user["xp"],
        "streak": user["streak"],
        "rank": user["rank"],
        "recent_activity": recent,
        "mastery": mastery
    })

@main.route("/api/save_stats", methods=["POST"])
def save_stats():
    # Only save stats if someone is actually logged in
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    
    # Check if this is a quiz completion
    if data.get("quiz_completed"):
        from .database import save_quiz_result
        save_quiz_result(
            session["user_id"],
            data.get("topic", "Unknown"),
            data.get("score", 0),
            data.get("total_questions", 0)
        )

    # Rank calculation logic (matches frontend)
    xp = data.get("xp", 0)
    rank = "Academy Student"
    if xp >= 1000: rank = "Hokage"
    elif xp >= 600: rank = "Jonin"
    elif xp >= 300: rank = "Chunin"
    elif xp >= 100: rank = "Genin"

    update_user_stats(
        session["user_id"], 
        data.get("score", 0), 
        xp, 
        data.get("streak", 0),
        rank
    )
    return jsonify({"message": "Progress saved!", "rank": rank})

# --- EXISTING: GENERATE & UPLOAD ROUTES ---

@main.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    topic = data.get("topic")
    difficulty = data.get("difficulty", "Medium")
    num_questions = data.get("num_questions", 5)

    quiz_data = generate_quiz(topic, num_questions)
    
    questions_list = quiz_data.get("quiz", [])
    save_quiz(topic, difficulty, json.dumps(questions_list))

    return jsonify(quiz_data)

@main.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        text_content = ""
        if filename.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                text_content = f.read()
        elif filename.endswith(".pdf"):
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            for page in reader.pages:
                text_content += page.extract_text()

        quiz_data = generate_quiz(text_content, 5)
        
        questions_list = quiz_data.get("quiz", [])
        save_quiz("Uploaded File", "Medium", json.dumps(questions_list))

        return jsonify(quiz_data)

    return jsonify({"error": "Invalid file type"}), 400