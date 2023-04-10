import datetime
from config import db


class ChatMessages(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    msg = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    datenow = datetime.datetime.now().strftime("%d %B %Y")
    timenow = datetime.datetime.now().strftime("%H:%M")
    date = db.Column(db.String)
    time = db.Column(db.String)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'))
