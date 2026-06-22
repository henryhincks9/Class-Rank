import os
import re
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db as sa_db, User as SAUser, Review as SAReview
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "app.db"
COURSES_FILE = DATA_DIR / "courses.json"
SCHOOL_EMAIL_DOMAIN = "@go.dsdmail.net"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_limits(name, default_csv):
    raw = os.environ.get(name, default_csv)
    limits = [part.strip() for part in raw.split(",") if part.strip()]
    return limits or [default_csv]

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev-secret-key"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=env_bool('SESSION_COOKIE_SECURE', False),
)

# SQLAlchemy setup (optional; keeps compatibility with existing sqlite file)
app.config.setdefault('SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL') or f'sqlite:///{DB_FILE}')
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
sa_db.init_app(app)
with app.app_context():
    try:
        sa_db.create_all()
    except Exception:
        # migrations may be used instead
        pass

# Rate limiter
limiter_storage = os.environ.get('REDIS_URL') or os.environ.get('LIMITER_STORAGE_URI')
default_limits = env_limits('RATE_LIMIT_DEFAULTS', '200 per day,50 per hour')
register_limit = os.environ.get('RATE_LIMIT_REGISTER', '5 per minute')
login_limit = os.environ.get('RATE_LIMIT_LOGIN', '10 per minute')
review_post_limit = os.environ.get('RATE_LIMIT_REVIEW_POST', '30 per hour')


def rate_limit_key():
    user_id = session.get('user_id')
    if user_id is not None:
        return f"user:{user_id}"
    forwarded_for = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    ip = forwarded_for or get_remote_address() or 'unknown'
    return f"ip:{ip}"


def login_rate_limit_key():
    payload = request.get_json(silent=True) or {}
    identifier = str(payload.get('username', '')).strip().lower() or 'anonymous'
    forwarded_for = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    ip = forwarded_for or get_remote_address() or 'unknown'
    return f"login:{ip}:{identifier}"


def register_rate_limit_key():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get('email', '')).strip().lower()
    username = str(payload.get('username', '')).strip().lower()
    identifier = email or username or 'anonymous'
    forwarded_for = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    ip = forwarded_for or get_remote_address() or 'unknown'
    return f"register:{ip}:{identifier}"


if limiter_storage:
    limiter = Limiter(key_func=rate_limit_key, storage_uri=limiter_storage, default_limits=default_limits)
else:
    limiter = Limiter(key_func=rate_limit_key, default_limits=default_limits)
limiter.init_app(app)


def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            enjoyment INTEGER NOT NULL,
            workload INTEGER NOT NULL,
            review TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()

    cursor.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cursor.fetchall()]
    if "email" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Ensure 'flagged' column exists on reviews for moderation
    cursor.execute("PRAGMA table_info(reviews)")
    cols = [r[1] for r in cursor.fetchall()]
    if "flagged" not in cols:
        cursor.execute("ALTER TABLE reviews ADD COLUMN flagged INTEGER DEFAULT 0")
        conn.commit()

    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            ("admin", f"admin{SCHOOL_EMAIL_DOMAIN}", generate_password_hash("admin123"), "admin", datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    conn.close()


def row_to_dict(row):
    return dict(row) if row is not None else None


def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email))


def is_davis_district_email(email):
    if not is_valid_email(email):
        return False
    return email.strip().lower().endswith(SCHOOL_EMAIL_DOMAIN)


def get_user_by_username(username):
    # prefer SQLAlchemy if available
    try:
        u = SAUser.query.filter_by(username=username).first()
        return {"id": u.id, "username": u.username, "email": u.email, "password_hash": u.password_hash, "role": u.role, "created_at": u.created_at} if u else None
    except Exception:
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        return row_to_dict(row)


def get_user_by_email(email):
    try:
        u = SAUser.query.filter_by(email=email).first()
        return {"id": u.id, "username": u.username, "email": u.email, "password_hash": u.password_hash, "role": u.role, "created_at": u.created_at} if u else None
    except Exception:
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        return row_to_dict(row)


def get_user_by_id(user_id):
    try:
        u = sa_db.session.get(SAUser, int(user_id))
        return {"id": u.id, "username": u.username, "email": u.email, "password_hash": u.password_hash, "role": u.role, "created_at": u.created_at} if u else None
    except Exception:
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return row_to_dict(row)


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return get_user_by_id(user_id)


def load_courses():
    with COURSES_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_reviews(course_id=None):
    try:
        query = SAReview.query.join(SAUser, SAReview.user_id == SAUser.id).add_columns(SAReview.id, SAReview.course_id, SAReview.user_id, SAUser.username, SAReview.difficulty, SAReview.enjoyment, SAReview.workload, SAReview.review, SAReview.created_at, SAReview.flagged)
        if course_id is not None:
            query = query.filter(SAReview.course_id == int(course_id))
        rows = query.order_by(SAReview.created_at.desc()).all()
        results = []
        for r in rows:
            # r is a tuple-like from add_columns; last element is flagged
            # normalize to dict
            results.append({
                'id': r.id,
                'course_id': r.course_id,
                'user_id': r.user_id,
                'username': r.username,
                'difficulty': r.difficulty,
                'enjoyment': r.enjoyment,
                'workload': r.workload,
                'review': r.review,
                'created_at': r.created_at,
                'flagged': r.flagged,
            })
        return results
    except Exception:
        conn = get_db()
        query = "SELECT r.id, r.course_id, r.user_id, u.username, r.difficulty, r.enjoyment, r.workload, r.review, r.created_at, r.flagged FROM reviews r JOIN users u ON r.user_id = u.id"
        params = []
        if course_id is not None:
            query += " WHERE r.course_id = ?"
            params.append(course_id)
        query += " ORDER BY r.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [row_to_dict(row) for row in rows]


def add_review(course_id, user_id, difficulty, enjoyment, workload, review_text):
    try:
        r = SAReview(course_id=course_id, user_id=user_id, difficulty=difficulty, enjoyment=enjoyment, workload=workload, review=review_text, created_at=datetime.now(timezone.utc).isoformat())
        sa_db.session.add(r)
        sa_db.session.commit()
        return r.id
    except Exception:
        conn = get_db()
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (course_id, user_id, difficulty, enjoyment, workload, review, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (course_id, user_id, difficulty, enjoyment, workload, review_text, created_at),
        )
        conn.commit()
        review_id = cursor.lastrowid
        conn.close()
        return review_id


def is_valid_username(username):
    return bool(re.match(r"^[A-Za-z0-9_.-]{3,30}$", username))


def is_valid_password(password):
    return len(password) >= 6


def get_rankings():
    courses = load_courses()
    reviews = load_reviews()
    ranking_data = []

    for course in courses:
        course_reviews = [review for review in reviews if review["course_id"] == course.get("id")]
        average_rating = 0
        if course_reviews:
            average_rating = sum((review["difficulty"] + review["enjoyment"] + review["workload"]) / 3 for review in course_reviews) / len(course_reviews)
        ranking_data.append({
            "course": course,
            "averageRating": round(average_rating, 2),
            "reviewCount": len(course_reviews),
        })

    ranking_data.sort(key=lambda item: (-item["averageRating"], -item["reviewCount"], item["course"].get("name", "")))
    return ranking_data[:10]




@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/me", methods=["GET"])
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": {"id": user["id"], "username": user["username"], "email": user.get("email"), "role": user["role"]}})


@app.route("/api/register", methods=["POST"])
@limiter.limit(register_limit, key_func=register_rate_limit_key)
def register():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    email = payload.get("email", "").strip().lower()
    if not username or not password or not email:
        return jsonify({"message": "Username, password, and school email are required."}), 400
    if not is_valid_username(username):
        return jsonify({"message": "Username must be 3-30 chars (letters, numbers, _.-)."}), 400
    if not is_valid_password(password):
        return jsonify({"message": "Password must be at least 6 characters."}), 400
    if not is_davis_district_email(email):
        return jsonify({"message": f"A valid Davis School District email ({SCHOOL_EMAIL_DOMAIN}) is required."}), 400
    if get_user_by_username(username):
        return jsonify({"message": "Username already exists."}), 400
    conn = get_db()
    if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
        conn.close()
        return jsonify({"message": "That email is already in use."}), 400
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, email, generate_password_hash(password), "user", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    session["user_id"] = user_id
    return jsonify({"message": "User registered.", "user": {"id": user_id, "username": username, "email": email, "role": "user"}})



@app.route("/api/login", methods=["POST"])
@limiter.limit(login_limit, key_func=login_rate_limit_key)
def login():
    payload = request.get_json(silent=True) or {}
    login_value = payload.get("username", "").strip()
    password = payload.get("password", "")
    if "@" in login_value:
        user = get_user_by_email(login_value.lower())
    else:
        user = get_user_by_username(login_value)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Invalid username/email or password."}), 401

    session["user_id"] = user["id"]
    return jsonify({"message": "Login successful.", "user": {"id": user["id"], "username": user["username"], "email": user.get("email"), "role": user["role"]}})


@app.route("/api/logout", methods=["GET"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out."})


@app.route("/api/courses", methods=["GET"])
def get_courses():
    return jsonify(load_courses())


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    course = next((course for course in load_courses() if course.get("id") == course_id), None)
    if course is None:
        return jsonify({"message": "Course not found"}), 404
    return jsonify(course)


@app.route("/api/reviews", methods=["GET", "POST"])
@limiter.limit(review_post_limit, methods=["POST"])
def reviews():
    if request.method == "GET":
        course_id = request.args.get("courseId", type=int)
        flagged = request.args.get("flagged")
        results = load_reviews(course_id)
        if flagged is not None:
            # filter flagged status (expects '1' or '0')
            try:
                f = int(flagged)
                results = [r for r in results if int(r.get("flagged", 0)) == f]
            except ValueError:
                pass
        return jsonify(results)

    user = current_user()
    if not user:
        return jsonify({"message": "Authentication required."}), 401

    payload = request.get_json(silent=True) or {}
    required = ["courseId", "difficulty", "enjoyment", "workload", "review"]
    if not all(key in payload for key in required):
        return jsonify({"message": "Missing fields."}), 400

    # Validate course exists
    course_id = int(payload["courseId"])
    if not any(c.get("id") == course_id for c in load_courses()):
        return jsonify({"message": "Course not found."}), 400

    difficulty = int(payload["difficulty"])
    enjoyment = int(payload["enjoyment"])
    workload = int(payload["workload"])
    if not (1 <= difficulty <= 5 and 1 <= enjoyment <= 5 and 1 <= workload <= 5):
        return jsonify({"message": "Ratings must be between 1 and 5."}), 400

    review_text = str(payload["review"]).strip()
    if len(review_text) > 2000:
        return jsonify({"message": "Review too long."}), 400
    if not user.get("email") or not is_davis_district_email(user["email"]):
        return jsonify({"message": f"A valid Davis School District email ({SCHOOL_EMAIL_DOMAIN}) is required to post a review."}), 403

    review_id = add_review(
        course_id,
        int(user["id"]),
        difficulty,
        enjoyment,
        workload,
        review_text,
    )
    return jsonify({"message": "Review added.", "id": review_id}), 201


@app.route("/api/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    user = current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"message": "Admin access required."}), 403

    conn = get_db()
    conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Review deleted."})


@app.route("/api/reviews/<int:review_id>/flag", methods=["POST"])
def flag_review(review_id):
    user = current_user()
    if not user:
        return jsonify({"message": "Authentication required."}), 401

    conn = get_db()
    row = conn.execute("SELECT id, flagged FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"message": "Review not found."}), 404
    new_flag = 1 if int(row["flagged"]) == 0 else 0
    conn.execute("UPDATE reviews SET flagged = ? WHERE id = ?", (new_flag, review_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Flag updated.", "flagged": new_flag})


@app.route("/api/admin/users", methods=["GET"])
def admin_list_users():
    user = current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"message": "Admin access required."}), 403

    conn = get_db()
    rows = conn.execute("SELECT id, username, email, role, created_at FROM users ORDER BY id").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/admin/users/<int:user_id>/role", methods=["POST"])
def admin_change_role(user_id):
    user = current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"message": "Admin access required."}), 403

    payload = request.get_json(silent=True) or {}
    role = payload.get("role")
    if role not in ("user", "teacher", "admin"):
        return jsonify({"message": "Invalid role."}), 400

    conn = get_db()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Role updated."})


@app.route("/api/rankings", methods=["GET"])
def rankings():
    return jsonify(get_rankings())


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.after_request
def set_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    response.headers.setdefault('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';")
    if env_bool('SESSION_COOKIE_SECURE', False):
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(ROOT, path)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5500, debug=env_bool('FLASK_DEBUG', True))
