import os
from base64 import b64encode
from datetime import datetime

import pytz


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or b64encode(os.urandom(24)).decode()
    CI_SECURITY = True if os.environ.get("ENVIRONMENT") == "prod" else False
    SESSION_COOKIE_SECURE = CI_SECURITY
    TOKEN_EXPIRY = 3600  # 1 hour = 3600 seconds


def today() -> datetime:
    now = datetime.now(tz=pytz.UTC)
    return datetime(year=now.year, month=now.month, day=now.day, tzinfo=pytz.UTC)
