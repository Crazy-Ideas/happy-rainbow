from typing import Optional

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import InputRequired, ValidationError

from models import User


class LoginForm(FlaskForm):
    ERROR_TEXT: str = "Invalid email or password."
    email: StringField = StringField("Email", validators=[InputRequired()])
    password: PasswordField = PasswordField("Password", validators=[InputRequired()])
    submit: SubmitField = SubmitField("Sign In")
    user: Optional[User] = None

    def validate_password(self, password: PasswordField):
        self.user = User.objects.filter_by(email=self.email.data).first()
        if not self.user:
            raise ValidationError(self.ERROR_TEXT)
        if not self.user.check_password(password.data):
            raise ValidationError(self.ERROR_TEXT)
        return
