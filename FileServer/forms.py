from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired()])
    password = StringField("패스워드", validators=[DataRequired()])