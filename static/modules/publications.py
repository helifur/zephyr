import datetime

from config import db


class Publication(db.Model):
    __tablename__ = 'publications'

    id = db.Column(db.Integer,
                   primary_key=True, autoincrement=True)
    content = db.Column(db.String, nullable=True)
    created_date = db.Column(db.DateTime,
                             default=datetime.datetime.now)
    is_private = db.Column(db.Boolean, default=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey("users.id"))

    likes_amount = db.Column(db.Integer, default=0)
    user = db.relationship('User')
