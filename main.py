from flask import Flask, flash, render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, logout_user

from static.modules.signup import RegisterForm
from static.modules.auth import LoginForm
from static.modules.edituser import EditUserForm
from static.modules.changeuserpass import ChangeUserPass
from static.modules.users import User
from static.modules.publications import Publication
from static.modules import db_session

# инициализируем приложения
app = Flask(__name__, template_folder="static/templates")
app.config['SECRET_KEY'] = 'zephyr_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

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
    return db_sess.get(User, user_id)


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


# профиль
@app.route('/profile/<int:id>')
def profile(id):
    db_sess = db_session.create_session()
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
def edit_profile(id):
    db_sess = db_session.create_session()

    form_useredit = EditUserForm()

    # POST
    if form_useredit.validate_on_submit():
        user = db_sess.query(User).filter(User.id == id).first()

        if db_sess.query(User).filter(User.email == form_useredit.email.data).first() and form_useredit.email.data != user.email:
            return render_template("edituser.html", cur_url=request.base_url.split('/')[-2],
                                   form_useredit=form_useredit, message="Пользователь с таким email-ом уже есть!")

        if not user.check_password(form_useredit.old_password.data):
            return render_template("edituser.html", cur_url=request.base_url.split('/')[-2],
                                   form_useredit=form_useredit, message="Неправильный текущий пароль!")

        if user:
            user.name = form_useredit.name.data
            user.surname = form_useredit.surname.data
            user.email = form_useredit.email.data
            f = request.files['newAvatar']
            print(f.read())

            db_sess.commit()
            return redirect(f'/profile/{id}')

    return render_template("edituser.html", cur_url=request.base_url.split('/')[-2], form_useredit=form_useredit)


# смена пароля
@app.route('/change_pass/<int:id>', methods=['GET', 'POST'])
def ch_pass(id):
    db_sess = db_session.create_session()

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
            return redirect(f'/profile/{id}')

    return render_template("chuserpass.html", cur_url=request.base_url.split('/')[-2], form_chpass=form_chpass)


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

        db_sess = db_session.create_session()
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
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form_auth.email.data).first()

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
