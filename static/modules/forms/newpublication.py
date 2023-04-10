from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class NewPublForm(FlaskForm):
    content = TextAreaField('Текст', validators=[DataRequired()])
    is_private = BooleanField('Приватный пост')
    submit = SubmitField('Создать')
