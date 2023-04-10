from flask import url_for
from config import db

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

followers = db.Table('followers',
                     db.metadata,
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('users.id')),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('users.id'))
                     )


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=True)
    surname = db.Column(db.String, nullable=True)
    email = db.Column(db.String,
                      index=True, unique=True, nullable=True)
    about = db.Column(db.String, default="No bio yet.")
    hashed_password = db.Column(db.String, nullable=True)
    reg_date = db.Column(db.DateTime,
                         default=datetime.datetime.now)

    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(
                                   followers.c.follower_id == id),
                               secondaryjoin=(
                                   followers.c.followed_id == id),
                               backref=db.orm.backref(
                                   'followers'),
                               lazy='dynamic')

    avatar = db.Column(db.LargeBinary, nullable=True)

    publications = db.relationship(
        "Publication", back_populates='user')

    author_id = db.relationship("ChatMessages")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def getAvatar(self, app, id):
        img = None
        db_avatar = db.session.query(
            User.avatar).filter(User.id == id).first()[0]
        if type(db_avatar) != bytes:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default_avatar.png'), "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: " + str(e))
        else:
            img = db_avatar

        return img

    def updateUserAvatar(self, avatar, user_id):
        if not avatar:
            return False

        db.session.query(User).filter(
            User.id == user_id).update({'avatar': avatar})
        db.session.commit()

        return True

    def follow(self, user):
        if not self.is_following(self, user):
            self.followed.append(user)
            db.session.add(self)
            db.session.commit()
            return True

    def unfollow(self, user):
        if self.is_following(self, user):
            self.followed.remove(user)
            db.session.add(self)
            db.session.commit()
            return True

    def is_following(self, cur_user, user):
        ans = db.session.query(followers).filter(
            followers.c.follower_id == cur_user.id, followers.c.followed_id == user.id).count()

        return ans

    def get_who_follow(self):
        data = db.session.query(followers).filter(
            followers.c.follower_id == self.id).all()
        return data

    def get_followers(self):
        data = db.session.query(followers).filter(
            followers.c.followed_id == self.id).all()
        return data
