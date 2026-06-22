import os
from server import init_db, get_db
from werkzeug.security import generate_password_hash
from datetime import datetime

ADMIN_USER = os.environ.get('FLASK_ADMIN_USER', 'admin')
ADMIN_PW = os.environ.get('FLASK_ADMIN_PW', None)

if __name__ == '__main__':
    init_db()
    if ADMIN_PW:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USER,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET password_hash = ?, role = ? WHERE username = ?", (generate_password_hash(ADMIN_PW), 'admin', ADMIN_USER))
        else:
            cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)", (ADMIN_USER, generate_password_hash(ADMIN_PW), 'admin', datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        print('Admin user set/updated.')
    else:
        print('No FLASK_ADMIN_PW set; ran init_db only.')

    # Optionally seed sample reviews from data/courses.json
    from pathlib import Path
    import json
    DATA_DIR = Path(__file__).resolve().parent / 'data'
    COURSES_FILE = DATA_DIR / 'courses.json'
    if COURSES_FILE.exists():
        conn = get_db()
        cur = conn.cursor()
        with COURSES_FILE.open('r', encoding='utf-8') as f:
            try:
                courses = json.load(f)
            except Exception:
                courses = []

        # Only seed if there are no reviews yet
        cur.execute('SELECT COUNT(*) as cnt FROM reviews')
        cnt = cur.fetchone()[0]
        if cnt == 0 and courses:
            print(f'Seeding sample reviews for {min(5, len(courses))} courses...')
            # Find or create a demo user
            cur.execute("SELECT id FROM users WHERE username = ?", ('demo_user',))
            r = cur.fetchone()
            if r:
                demo_user_id = r[0]
            else:
                cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)", ('demo_user', generate_password_hash('demo_pass'), 'user', datetime.utcnow().isoformat()))
                demo_user_id = cur.lastrowid

            sample_texts = [
                'Great course, learned a lot.',
                'Challenging but rewarding.',
                'A bit heavy on the workload.',
                'Excellent instructor and materials.',
                'Would recommend to others.'
            ]
            import random
            for course in courses[:5]:
                course_id = course.get('id')
                if course_id is None:
                    continue
                difficulty = random.randint(2,4)
                enjoyment = random.randint(3,5)
                workload = random.randint(2,4)
                review_text = random.choice(sample_texts)
                created_at = datetime.utcnow().isoformat()
                cur.execute(
                    'INSERT INTO reviews (course_id, user_id, difficulty, enjoyment, workload, review, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (course_id, demo_user_id, difficulty, enjoyment, workload, review_text, created_at)
                )
            conn.commit()
            print('Sample reviews seeded.')
        conn.close()
