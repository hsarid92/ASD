from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    child_name = db.Column(db.String(150), nullable=False)
    child_id = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    diagnosis = db.Column(db.String(150), nullable=False)
    diagnosis_age = db.Column(db.Integer, nullable=False)
    educational_framework = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)  # Name of the contact
    relation = db.Column(db.String(50), nullable=False)  # e.g., Teacher, Parent, Therapist
    phone_number = db.Column(db.String(20), nullable=False)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # e.g., "Monday", "Tuesday"
    time_slot = db.Column(db.String(50), nullable=False)  # e.g., "08:00-10:00"
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    activity = db.Column(db.String(200), nullable=True)
    
    # Add relationship to Contact model
    contact = db.relationship('Contact', backref='schedules', lazy=True)
