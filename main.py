from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, logout_user

from static.modules.signup import RegisterForm
from static.modules.auth import LoginForm
from static.modules.users import User
from static.modules import db_session

# инициализируем приложения
app = Flask(__name__, template_folder="static/templates")
app.config['SECRET_KEY'] = 'zephyr_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

# инициализируем базу данных
db_session.global_init("static/db/data.db")


# получение пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


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


@app.route('/profile')
def profile():
    return render_template("profile.html", cur_url=request.base_url.split('/')[-1])


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
