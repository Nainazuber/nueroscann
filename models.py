from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), default='prefer_not_to_say')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    test_results = db.relationship('TestResult', backref='user', lazy=True)

class TestResult(db.Model):
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blink_count = db.Column(db.Integer, default=0)
    blink_rate = db.Column(db.Float, default=0.0)
    micro_expressions = db.Column(db.Text)  # JSON string
    conditions = db.Column(db.Text)  # JSON string
    confidence_scores = db.Column(db.Text)  # JSON string
    recommendations = db.Column(db.Text)  # JSON string
    facial_asymmetry = db.Column(db.Float, default=0.0)
    expression_variability = db.Column(db.Float, default=0.0)
    test_duration = db.Column(db.Integer, default=60)  # seconds
    test_date = db.Column(db.DateTime, default=datetime.utcnow)

class HealthCondition(db.Model):
    __tablename__ = 'health_conditions'
    
    id = db.Column(db.Integer, primary_key=True)
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_results.id'), nullable=False)
    condition_name = db.Column(db.String(100))
    confidence_score = db.Column(db.Float, default=0.0)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)