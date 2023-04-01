import sqlite3
from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase, create_session
import sqlalchemy
import datetime


class User(SqlAlchemyBase, UserMixin):
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
        # # self.__cur.execute(
        # #     f"UPDATE users SET avatar = ? WHERE id = ?", (binary, user_id))
        # # self.__db.commit()

        return True
