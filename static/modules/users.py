import os
from flask import url_for, Flask
from flask_sqlalchemy import SQLAlchemy
from config import db

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase, create_session
import sqlalchemy
import datetime

followers = sqlalchemy.Table('followers',
                             db.metadata,
                             sqlalchemy.Column('follower_id', sqlalchemy.Integer,
                                               sqlalchemy.ForeignKey('users.id')),
                             sqlalchemy.Column('followed_id', sqlalchemy.Integer,
                                               sqlalchemy.ForeignKey('users.id'))
                             )

# app = Flask(__name__, template_folder="/static/templates")
# app.config['SECRET_KEY'] = 'zephyr_secret_key'
# file_path = os.path.abspath(os.getcwd())+"\data.db"
# print(file_path)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path
# db = SQLAlchemy(app)
# with app.app_context():
#     db.create_all()
#     print("OK")
# pbkdf2: sha256: 260000$AJxsgfLOZKzYWD4G$a16c2c6e479228f2a65e2e1b7c0890f89203d8de0373e2d69d2d68e2e9734049
# 2023-03-28 20: 21: 38.216154


class User(db.Model, SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, default="No bio yet.")
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reg_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                 default=datetime.datetime.now)

    followed = sqlalchemy.orm.relationship('User',
                                           secondary=followers,
                                           primaryjoin=(
                                               followers.c.follower_id == id),
                                           secondaryjoin=(
                                               followers.c.followed_id == id),
                                           backref=sqlalchemy.orm.backref(
                                               'followers'),
                                           lazy='dynamic')

    avatar = sqlalchemy.Column(sqlalchemy.LargeBinary, nullable=True)

    publications = sqlalchemy.orm.relationship(
        "Publication", back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def getAvatar(self, app, id):
        db_sess = create_session()
        img = None
        db_avatar = db_sess.query(User.avatar).filter(User.id == id).first()[0]
        db_sess.close()
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
        db_sess = create_session()

        if not avatar:
            return False

        db_sess.query(User).filter(
            User.id == user_id).update({'avatar': avatar})
        db_sess.commit()
        db_sess.close()
        # # self.__cur.execute(
        # #     f"UPDATE users SET avatar = ? WHERE id = ?", (binary, user_id))
        # # self.__db.commit()

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
        # db_sess = create_session()
        # stmt = sqlalchemy.select(followers).filter(
        #     followers.c.followed_id == user.id).count() > 0
        # print(stmt)
        # subq = stmt.subquery()
        # ans = sqlalchemy.select(subq)
        ans = db.session.query(followers).filter(
            followers.c.follower_id == cur_user.id, followers.c.followed_id == user.id).count()

        print(ans)
        # ans = db_sess.query(followers).filter(
        #     followers.c.followed_id == user.id).count() > 0
        # db_sess.close()

        return ans

    def get_who_follow(self):
        data = db.session.query(followers).filter(
            followers.c.follower_id == self.id).all()
        return data

    def get_followers(self):
        data = db.session.query(followers).filter(
            followers.c.followed_id == self.id).all()
        return data
