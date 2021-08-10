import os
from datetime import datetime
from typing import Optional

import pytz
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


def get_user_from_token(token: str) -> Optional[User]:
    user: User = User.objects.filter_by(token=token).first()
    if not user:
        return None
    if user.token_expiration < datetime.now(tz=pytz.UTC):
        return None
    return user


if __name__ == '__main__':
    app.run()

# noinspection PyUnresolvedReferences
from routes import *


@app.shell_context_processor
def make_shell_context() -> dict:
    from models import Workshop
    return {
        "User": User,
        "Workshop": Workshop,
        "Config": Config,
        "today": today
    }
