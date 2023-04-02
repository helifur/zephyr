import datetime
import os
from flask import Flask, flash, render_template, redirect, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin

import sqlalchemy
from static.modules.signup import RegisterForm
from static.modules.auth import LoginForm
from static.modules.edituser import EditUserForm
from static.modules.changeuserpass import ChangeUserPass
from static.modules.users import User
from config import app, login_manager, db
from static.modules.publications import Publication
from static.modules import db_session


# инициализируем базу данных
db_session.global_init("static/db/data.db")
db_sess = db_session.create_session()
# publ = Publication(content="Всем привет!", user_id=1, is_private=False)
# db_sess.add(publ)
# db_sess.commit()


# class User(db.Model, UserMixin):
#     __tablename__ = 'users'

#     id = sqlalchemy.Column(sqlalchemy.Integer,
#                            primary_key=True, autoincrement=True)
#     name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
#     surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
#     email = sqlalchemy.Column(sqlalchemy.String,
#                               index=True, unique=True, nullable=True)
#     about = sqlalchemy.Column(sqlalchemy.String, default="No bio yet.")
#     hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
#     reg_date = sqlalchemy.Column(sqlalchemy.DateTime,
#                                  default=datetime.datetime.now)

#     followed = sqlalchemy.orm.relationship('User',
#                                            secondary=followers,
#                                            primaryjoin=(
#                                                followers.c.follower_id == id),
#                                            secondaryjoin=(
#                                                followers.c.followed_id == id),
#                                            backref=sqlalchemy.orm.backref(
#                                                'followers'),
#                                            lazy='dynamic')

#     avatar = sqlalchemy.Column(sqlalchemy.LargeBinary, nullable=True)

#     # publications = sqlalchemy.orm.relationship(
#     #     "Publication", back_populates='user')

#     def set_password(self, password):
#         self.hashed_password = generate_password_hash(password)

#     def check_password(self, password):
#         return check_password_hash(self.hashed_password, password)

#     def getAvatar(self, app, id):
#         db_sess = create_session()
#         img = None
#         db_avatar = db_sess.query(User.avatar).filter(User.id == id).first()[0]
#         db_sess.close()
#         if type(db_avatar) != bytes:
#             try:
#                 with app.open_resource(app.root_path + url_for('static', filename='images/default_avatar.png'), "rb") as f:
#                     img = f.read()
#             except FileNotFoundError as e:
#                 print("Не найден аватар по умолчанию: " + str(e))
#         else:
#             img = db_avatar

#         return img

#     def updateUserAvatar(self, avatar, user_id):
#         db_sess = create_session()

#         if not avatar:
#             return False

#         db_sess.query(User).filter(
#             User.id == user_id).update({'avatar': avatar})
#         db_sess.commit()
#         db_sess.close()
#         # # self.__cur.execute(
#         # #     f"UPDATE users SET avatar = ? WHERE id = ?", (binary, user_id))
#         # # self.__db.commit()

#         return True

#     def follow(self, user):
#         if not self.is_following(user):
#             self.followed.append(user)
#             db.session.add(self)
#             db.session.commit()
#             return True

#     def unfollow(self, user):
#         if self.is_following(user):
#             self.followed.remove(user)
#             return self

#     def is_following(self, user):
#         db_sess = db_session.create_session()
#         # stmt = sqlalchemy.select(followers).filter(
#         #     followers.c.followed_id == user.id).count() > 0
#         # print(stmt)
#         # subq = stmt.subquery()
#         # ans = sqlalchemy.select(subq)
#         ans = db_sess.query(followers).filter(
#             followers.c.followed_id == user.id).count() > 0
#         db_sess.close()
#         return ans


# with app.app_context():
#     db.create_all()
#     print("OK")

# user = User(name="Vasya", surname="Poopkin", email="sjmdfi@gmail.com")
# db.session.add(user)
# db.session.commit()
# получение пользователя


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    ans = db_sess.get(User, user_id)
    db_sess.close()
    return ans


# выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# главная страница
@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", cur_url=request.base_url.split('/')[-1])


"""==========ПОЛЬЗОВАТЕЛЬ/АВАТАРЫ=============="""


# получить аватар
@app.route('/userava/<int:id>')
@login_required
def userava(id):
    img = current_user.getAvatar(app, id)

    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


# смена аватара
@app.route('/change_avatar/<int:id>', methods=["GET", "POST"])
@login_required
def new_avatar(id):
    if request.method == "POST":
        # db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()

        file = request.files['newAvatar']
        ext = file.filename.rsplit('.', 1)[1]
        print(ext)
        if ext == "png" or ext == "PNG" or ext == "jpg" or ext == "JPG":
            user.updateUserAvatar(file.read(), user.id)
            return redirect(f'/profile/{current_user.id}')

    return render_template("editavatar.html", cur_url=request.base_url.split('/')[-2])


# профиль
@app.route('/profile/<int:id>')
@login_required
def profile(id):
    # db_sess = db_session.create_session()
    personal_data = db_sess.query(
        User.name, User.surname, User.about).filter(User.id == id).one()
    publications = db_sess.query(Publication).filter(Publication.is_private != True,
                                                     Publication.user_id == id)

    return render_template("profile.html",
                           cur_url=request.base_url.split('/')[-2],
                           id=id,
                           publications=publications,
                           name=personal_data[0],
                           surname=personal_data[1],
                           about=personal_data[2])


# редактирование профиля
@app.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    # db_sess = db_session.create_session()

    form_useredit = EditUserForm()

    # POST
    if form_useredit.validate_on_submit():
        user = db_sess.query(User).filter(User.id == id).first()

        if db_sess.query(User).filter(User.email == form_useredit.email.data).first() and form_useredit.email.data != user.email:
            return render_template("edituser.html", cur_url=request.base_url.split('/')[-2],
                                   form_useredit=form_useredit, message="Пользователь с таким email-ом уже есть!")

        # if not user.check_password(form_useredit.old_password.data):
        #     return render_template("edituser.html", cur_url=request.base_url.split('/')[-2],
        #                            form_useredit=form_useredit, message="Неправильный текущий пароль!")

        if user:
            user.name = form_useredit.name.data
            user.surname = form_useredit.surname.data
            user.email = form_useredit.email.data

        db_sess.commit()
        # db_sess.close()
        return redirect(f'/profile/{id}')

    return render_template("edituser.html", cur_url=request.base_url.split('/')[-2], form_useredit=form_useredit)


# смена пароля
@app.route('/change_pass/<int:id>', methods=['GET', 'POST'])
@login_required
def ch_pass(id):
    # db_sess = db_session.create_session()

    form_chpass = ChangeUserPass()

    if form_chpass.validate_on_submit():
        user = db_sess.query(User).filter(User.id == id).first()

        if not user.check_password(form_chpass.old_password.data):
            return render_template("chuserpass.html", cur_url=request.base_url.split('/')[-2],
                                   form_chpass=form_chpass, message="Неправильный текущий пароль!")

        if form_chpass.new_password.data != form_chpass.new_password_repeat.data:
            return render_template("chuserpass.html", cur_url=request.base_url.split('/')[-2],
                                   form_chpass=form_chpass, message="Пароли не совпадают!")

        if user:
            user.set_password(form_chpass.new_password.data)

            db_sess.commit()
            # db_sess.close()
            return redirect(f'/profile/{id}')

    return render_template("chuserpass.html", cur_url=request.base_url.split('/')[-2], form_chpass=form_chpass)


"""============END PROFILE==================="""


# список всех пользователей
@app.route('/members')
def members():
    # db_sess = db_session.create_session()

    data = db_sess.query(User).all()

    return render_template("members.html", data=data)


# список всех пользователей
@app.route('/friends')
def friends():
    who_follow_data = current_user.get_who_follow()
    who_follow_data = [db.session.query(User).filter(User.id == item[1]).first()
                       for item in who_follow_data]

    followers_data = current_user.get_followers()
    followers_data = [db.session.query(User).filter(User.id == item[0]).first()
                      for item in followers_data]

    # вхождение пользователя и в подписки, и в подписчики
    friends_data = list(set(who_follow_data) & set(followers_data))

    no_subscribes = not bool(set(who_follow_data) - set(friends_data))
    no_subscribers = not bool(set(followers_data) - set(friends_data))

    return render_template("friends.html",
                           cur_url=request.base_url.split('/')[-1],
                           who_follow_data=who_follow_data,
                           followers_data=followers_data,
                           friends_data=friends_data,
                           no_subscribes=no_subscribes,
                           no_subscribers=no_subscribers
                           )


# добавить в друзья
@app.route('/add_friend/<int:id>')
def add_friend(id):
    # db_sess_1 = db_session.create_session()
    # filter(User.id == id).
    user = db.session.query(User).filter(User.id == id).first()
    print(user)
    # db_sess.close()
    g = current_user.follow(user)

    # sqlalchemy.orm.session.add(g)
    # db_sess_1.commit()
    # db_sess_1.close()
    return redirect("/friends")


# отписаться
@app.route('/remove_friend/<int:id>')
def remove_friend(id):
    # db_sess_1 = db_session.create_session()
    # filter(User.id == id).
    user = db.session.query(User).filter(User.id == id).first()
    print(user)
    # db_sess.close()
    g = current_user.unfollow(user)

    # sqlalchemy.orm.session.add(g)
    # db_sess_1.commit()
    # db_sess_1.close()
    return redirect("/friends")


# регистрация
@app.route('/signup', methods=['GET', 'POST'])
def register():
    form_reg = RegisterForm()

    if form_reg.validate_on_submit():
        if form_reg.password.data != form_reg.password_repeat.data:
            return render_template('signup.html', title='Регистрация',
                                   cur_url=request.base_url.split('/')[-1],
                                   form_reg=form_reg,
                                   message="Пароли не совпадают")

        # db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form_reg.email.data).first():
            return render_template('signup.html', title='Регистрация',
                                   cur_url=request.base_url.split('/')[-1],
                                   form_reg=form_reg,
                                   message="Такой пользователь уже есть")

        user = User(
            name=form_reg.name.data,
            surname=form_reg.surname.data,
            email=form_reg.email.data,
        )

        user.set_password(form_reg.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect('/auth')

    return render_template('signup.html', cur_url=request.base_url.split('/')[-1], title='Регистрация', form_reg=form_reg)


# вход в систему
@app.route('/auth', methods=['GET', 'POST'])
def login():
    form_auth = LoginForm()

    if form_auth.validate_on_submit():
        # db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form_auth.email.data).first()

        db_sess.close()

        if user and user.check_password(form_auth.password.data):
            login_user(user, remember=form_auth.remember_me.data)
            return redirect("/")

        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               cur_url=request.base_url.split('/')[-1],
                               form_auth=form_auth)

    return render_template('login.html', cur_url=request.base_url.split('/')[-1], title='Авторизация', form_auth=form_auth)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
