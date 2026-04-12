from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Model for storing user accounts"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to consultations
    consultations = db.relationship('Consultation', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Consultation(db.Model):
    """Model for storing user consultations"""
    __tablename__ = 'consultations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Optional user link
    patient_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    predicted_disease = db.Column(db.String(200), nullable=False)
    recommended_specialization = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Consultation {self.id} - {self.patient_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_name': self.patient_name,
            'age': self.age,
            'gender': self.gender,
            'symptoms': self.symptoms,
            'predicted_disease': self.predicted_disease,
            'recommended_specialization': self.recommended_specialization,
            'token': self.token,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def generate_token(min_value: int = 0, max_value: int = 999999) -> str:
        """
        Generate a numeric token as a 6-digit string (e.g., "003451").

        Note: `token` is unique in DB. Callers can retry if a rare collision occurs.
        """
        if min_value < 0 or max_value > 999999 or min_value > max_value:
            min_value, max_value = 0, 999999
        n = secrets.randbelow(max_value - min_value + 1) + min_value
        return str(n).zfill(6)

class MedicalCamp(db.Model):
    """Model for storing medical camp information"""
    __tablename__ = 'medical_camps'
    
    id = db.Column(db.Integer, primary_key=True)
    camp_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(300), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(50), nullable=False)
    services_offered = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MedicalCamp {self.id} - {self.camp_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'camp_name': self.camp_name,
            'location': self.location,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'time': self.time,
            'services_offered': self.services_offered,
            'contact_info': self.contact_info,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

