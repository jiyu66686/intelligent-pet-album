from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.Enum('admin', 'user'), default='user')
    created_at = db.Column(db.DateTime, default=datetime.now)

    photos = db.relationship('PetPhoto', backref='user', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('OperationLog', backref='user', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class PetPhoto(db.Model):
    __tablename__ = 'pet_photos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    photo_url = db.Column(db.String(500), nullable=False)
    pet_type = db.Column(db.String(20))  # cat / dog / other / unknown
    pet_breed = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    photo_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    upload_time = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    likes_relation = db.relationship('Like', backref='photo', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'photo_url': self.photo_url,
            'pet_type': self.pet_type,
            'pet_breed': self.pet_breed,
            'confidence': self.confidence,
            'photo_name': self.photo_name,
            'description': self.description,
            'likes': self.likes,
            'upload_time': self.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('pet_photos.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (db.UniqueConstraint('user_id', 'photo_id', name='unique_user_photo_like'),)


class OperationLog(db.Model):
    __tablename__ = 'operation_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(20), nullable=False)
    target_table = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'System',
            'action': self.action,
            'target_table': self.target_table,
            'target_id': self.target_id,
            'detail': self.detail,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }