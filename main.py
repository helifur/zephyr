from flask import render_template, redirect, request, make_response
from flask_login import login_required, login_user, logout_user, current_user

from static.modules.signup import RegisterForm
from static.modules.auth import LoginForm
from static.modules.edituser import EditUserForm
from static.modules.changeuserpass import ChangeUserPass
from static.modules.newpublication import NewPublForm
from static.modules.editpubl import EditPublForm

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
@app.route('/profile/<int:id>', methods=["GET", "POST"])
@login_required
def profile(id):
    # db_sess = db_session.create_session()
    personal_data = db_sess.query(
        User.name, User.surname, User.about).filter(User.id == id).one()

    if id == current_user.id:
        publications = db_sess.query(Publication).filter(
            Publication.user_id == id)
    else:
        publications = db_sess.query(Publication).filter(Publication.is_private != True,
                                                         Publication.user_id == id)

    likes = request.cookies.get("likes", [])

    # если лайки это пустая строка, то делаем из нее пустой список
    # иначе будет ошибка TypeError
    if not likes:
        likes = []

    else:
        likes = [int(item) for item in likes.split(' ')]

    print(likes)

    return render_template("profile.html",
                           cur_url=request.base_url.split('/')[-2],
                           id=id,
                           publications=publications,
                           name=personal_data[0],
                           surname=personal_data[1],
                           about=personal_data[2],
                           likes=likes)


# поставить лайк
@app.route('/profile/make_like/<int:publ_id>/<int:user_id>')
def make_like(publ_id, user_id):
    likes = request.cookies.get("likes", 0)
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    if likes:
        likes = [item for item in likes.split(' ')]
        print(likes)

        if str(publ_id) in likes:
            likes.remove(str(publ_id))
            db.session.query(Publication).filter(Publication.id == publ_id).update(
                {'likes_amount': Publication.likes_amount - 1})
            db.session.commit()
            res = make_response(redirect(f'/{referrer}'))
            res.set_cookie("likes", ' '.join(likes),
                           max_age=60 * 60 * 24 * 365 * 2)

        else:
            likes.append(str(publ_id))
            db.session.query(Publication).filter(Publication.id == publ_id).update(
                {'likes_amount': Publication.likes_amount + 1})
            db.session.commit()
            res = make_response(redirect(f'/{referrer}'))
            res.set_cookie("likes", ' '.join(likes),
                           max_age=60 * 60 * 24 * 365 * 2)

    else:
        res = make_response(redirect(f'/{referrer}'))
        db.session.query(Publication).filter(Publication.id == publ_id).update(
            {'likes_amount': Publication.likes_amount + 1})
        db.session.commit()
        res.set_cookie("likes", f'{publ_id}',
                       max_age=60 * 60 * 24 * 365 * 2)

    return res


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
            user.about = form_useredit.about.data

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


"""============PUBLICATIONS========="""


# добавить публикации
@app.route('/new_publication/<int:id>', methods=["GET", "POST"])
def new_publication(id):
    form_publ = NewPublForm()

    if form_publ.validate_on_submit():
        publ = Publication(content=form_publ.content.data,
                           is_private=form_publ.is_private.data,
                           user_id=current_user.id)

        db.session.add(publ)
        db.session.commit()

        return redirect(f"/profile/{current_user.id}")

    return render_template("newpubl.html", form_publ=form_publ)


# изменить публикацию
@app.route('/edit_publication/<int:id>', methods=["GET", "POST"])
def edit_publication(id):
    form_edit_publ = EditPublForm()
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    publ = db.session.query(Publication).filter(Publication.id == id,
                                                Publication.user_id == current_user.id).first()

    form_edit_publ.content.data = publ.content

    # защита от дурака, если человек вручную впишет адрес в строку браузера
    # у него не получится изменить чужую публикацию
    if publ:
        if form_edit_publ.validate_on_submit():
            db.session.query(Publication).filter(Publication.id == id,
                                                 Publication.user_id == current_user.id).update({"content": form_edit_publ.content.data,
                                                                                                "is_private": form_edit_publ.is_private.data,
                                                                                                 "edited_date": None})
            db.session.commit()

            return redirect(f"/profile/{current_user.id}")

        return render_template("editpubl.html", form_edit_publ=form_edit_publ, publ=publ)

    else:
        return redirect(f'/{referrer}')


# удалить публикацию
@app.route('/delete_publication/<int:id>', methods=["GET", "POST"])
def delete_publication(id):
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    publ = db.session.query(Publication).filter(Publication.id == id,
                                                Publication.user_id == current_user.id).first()

    # защита от дурака, если человек вручную впишет адрес в строку браузера
    # у него не получится изменить чужую публикацию
    if publ:
        db.session.query(Publication).filter(Publication.id == id,
                                             Publication.user_id == current_user.id).delete()
        db.session.commit()

        return redirect(f"/profile/{current_user.id}")

    else:
        return redirect(f'/{referrer}')


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
    app.run(port=8080, host='localhost', debug=True)
