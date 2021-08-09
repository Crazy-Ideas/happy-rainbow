import os
from base64 import b64encode
from datetime import datetime, timedelta

import pytz
from firestore_ci import FirestoreDocument
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config


class User(FirestoreDocument, UserMixin):

    def __init__(self):
        super().__init__()
        self.email: str = str()
        self.password_hash: str = str()
        self.token: str = str()
        self.token_expiration: datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)

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
