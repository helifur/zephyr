from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = EmailField('Адрес эл. почты', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_repeat = PasswordField(
        'Повторите пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')
