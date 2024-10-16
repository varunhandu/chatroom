from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    time = db.Column(db.String, default=datetime.now().strftime('%H:%M'))
    room_id = db.Column(db.Integer, db.ForeignKey('chatroom.id'))

class Chatroom(db.Model):
    __tablename__ = 'chatroom'

    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String, nullable=False)
    messages = db.relationship('Message')
    
