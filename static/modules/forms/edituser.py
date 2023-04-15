from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired


class EditUserForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = EmailField('Адрес эл. почты', validators=[DataRequired()])
    about = StringField('О себе')
    submit = SubmitField('Подтвердить')
