from config import db


class Chats(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    allowed_users = db.Column(db.String(256))
    is_unread = db.Column(db.Boolean, default=0)

    msg_id = db.relationship("ChatMessages")
