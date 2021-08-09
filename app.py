import os
from typing import Optional

from flask import Flask
from flask_login import LoginManager

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-cloud.json"

from config import Config
from models import User

app = Flask(__name__)
app.config.from_object(Config)

login = LoginManager(app)
login.login_view = "login"
login.session_protection = "strong" if Config.CI_SECURITY else "basic"


@login.user_loader
def load_user(email: str) -> Optional[User]:
    user: User = User.objects.filter_by(email=email).first()
    return user


if __name__ == '__main__':
    app.run()

# noinspection PyUnresolvedReferences
from routes import *


@app.shell_context_processor
def make_shell_context() -> dict:
    return {
        "User": User,
    }
