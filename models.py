import os
import random
import string
from base64 import b64encode
from datetime import datetime, timedelta
from typing import List

import pytz
from firestore_ci import FirestoreDocument
from flask import request, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config, today


class Workshop(FirestoreDocument):

    def __init__(self):
        super().__init__()
        self.title: str = str()
        self.topic: str = str()
        self.date: datetime = today()
        self.time: str = str()
        self.instructor: str = str()
        self.venue: str = str()
        self.image_url: str = str()
        self.materials: List[str] = list()
        self.bg_color: int = 0xFFFFFF  # white
        self.signature: str = str()
        self.participants: int = 0
        self.url_expiration: datetime = today()

    @property
    def date_format(self) -> str:
        return self.date.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%a, %d-%b-%y")

    @property
    def valid_url(self) -> bool:
        if not self.signature:
            return False
        if self.url_expiration < datetime.now(tz=pytz.UTC):
            return False
        return True

    @property
    def url(self) -> str:
        return f"{request.host_url}{url_for('certificate_download', workshop_id=self.id, signature=self.signature)}"

    def generate_url(self) -> None:
        if self.valid_url:
            return
        self.signature: str = "".join(random.choices(string.ascii_letters + string.digits, k=128))
        self.url_expiration: datetime = datetime.now(tz=pytz.UTC) + timedelta(days=7)
        self.save()


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
        now: datetime = datetime.now(tz=pytz.UTC)
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
