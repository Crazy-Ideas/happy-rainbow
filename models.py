import os
from base64 import b64encode
from datetime import datetime, timedelta
from typing import List

import pytz
from firestore_ci import FirestoreDocument
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config, today


class Workshop(FirestoreDocument):

    def __init__(self):
        super().__init__()
        self.title: str = str()
        self.instructor: str = str()
        self.topic: str = str()
        self.date: datetime = today()
        self.time: str = str()
        self.venue: str = str()
        self.image_url: str = str()
        self.materials: List[str] = list()
        self.bg_color: int = 0xFFFFFF  # white

    @property
    def date_format(self) -> str:
        return self.date.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%a, %d-%b-%y")


Workshop.init()


class User(FirestoreDocument, UserMixin):

    def __init__(self):
        super().__init__()
        self.email: str = str()
        self.password_hash: str = str()
        self.token: str = str()
        self.token_expiration: datetime = datetime.now(tz=pytz.UTC)

    def __repr__(self):
        return self.email

    def get_id(self) -> str:
        return self.email

    def get_token(self, expires_in=Config.TOKEN_EXPIRY) -> str:
        now: datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token: str = b64encode(os.urandom(24)).decode()
        self.token_expiration: datetime = now + timedelta(seconds=expires_in)
        self.save()
        return self.token

    def revoke_token(self) -> None:
        self.token_expiration: datetime = datetime.utcnow() - timedelta(seconds=1)
        self.save()

    def set_password(self, password) -> None:
        self.password_hash: str = generate_password_hash(password)
        self.save()

    def check_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)


User.init()
