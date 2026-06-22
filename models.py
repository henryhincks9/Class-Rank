from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default='user')
    created_at = db.Column(db.String, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    enjoyment = db.Column(db.Integer, nullable=False)
    workload = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    flagged = db.Column(db.Integer, default=0)
