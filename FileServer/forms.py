from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired("아이디를 입력해주세요")])
    password = PasswordField("패스워드", validators=[DataRequired("패스워드를 입력해주세요")])


class SignupForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired("아이디를 입력해주세요"), Length(min = 3, max = 25)])
    password1 = PasswordField("비밀번호",validators=[DataRequired("비밀번호를 입력해주세요")
                                                    , EqualTo("password2", "비밀번호가 일치하지 않습니다")])
    password2 = PasswordField("비밀번호 확인", validators=[DataRequired("비밀번호 확인을 입력해주세요")])
    email = EmailField("이메일", validators=[DataRequired("이메일을 입력해주세요"), Email()])
    