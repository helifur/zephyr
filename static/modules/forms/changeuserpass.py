from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired


class ChangeUserPass(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    new_password_repeat = PasswordField(
        'Повторите новый пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
