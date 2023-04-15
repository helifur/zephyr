import datetime
from flask import url_for
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

from config import db

followers = db.Table('followers',
                     db.metadata,
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('users.id')),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('users.id'))
                     )


class User(db.Model, UserMixin):
    """Class representing the user"""

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
        """Set password to current user

        Args:
            password (str): new password
        """

        # generate password hash and set it to current user
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        """Checks whether the transmitted password matches the current one

        Args:
            password (str): password to be verified

        Returns:
            bool
        """
        return check_password_hash(self.hashed_password, password)

    def getAvatar(self, app, id):
        """Allows to get avatar of user with id
            equals to id argument

        Args:
            app (flask app): current flask app
            id (int): user id

        Returns:
            bytes: user avatar
        """

        # necessary avatar
        img = None
        # get avatar from db
        db_avatar = db.session.query(
            User.avatar).filter(User.id == id).first()[0]

        # if avatar was not set
        if not isinstance(db_avatar, bytes):
            # set this user default avatar
            try:
                with app.open_resource(app.root_path +
                                       url_for('static', filename='images/default_avatar.png'), "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Default avatar not found: " + str(e))
        # if avatar was set
        else:
            # set avatar from db
            img = db_avatar

        return img

    def updateUserAvatar(self, avatar, user_id):
        """Allows to update user avatar

        Args:
            avatar (PIL IMAGE): future avatar
            user_id (int): user id

        Returns:
            bool: success or error
        """

        # if avatar is incorrect
        if not avatar:
            return False

        # update avatar in db
        db.session.query(User).filter(
            User.id == user_id).update({'avatar': avatar})
        # commit changes
        db.session.commit()

        return True

    def follow(self, user):
        """Allows to follow user

        Args:
            user (User): user

        Returns:
            bool
        """

        # if current user not following user
        if not self.is_following(user):
            # add user to db followed column
            self.followed.append(user)
            db.session.add(self)
            db.session.commit()
            return True

    def unfollow(self, user):
        """Allows to unfollow user

        Args:
            user (User): user

        Returns:
            bool
        """

        # if its possible to unfollow user
        if self.is_following(user):
            # remove user from db followed column
            self.followed.remove(user)
            db.session.add(self)
            db.session.commit()
            return True

    def is_following(self, user):
        """Checks is the current user following to user arg

        Args:
            user (User): another user
        """

        # check if the id of the current user is in the follower column
        # and if there is an id of another user in the followed column
        ans = db.session.query(followers).filter(
            followers.c.follower_id == self.id, followers.c.followed_id == user.id).count()

        return ans

    def get_who_follow(self):
        """Get list of users followed by current user

        Returns:
            list: list of users
        """

        data = db.session.query(followers).filter(
            followers.c.follower_id == self.id).all()
        return data

    def get_followers(self):
        """Get list of users who follow current user

        Returns:
            list: list of users
        """

        data = db.session.query(followers).filter(
            followers.c.followed_id == self.id).all()
        return data
