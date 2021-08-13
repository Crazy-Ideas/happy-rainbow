import os
from base64 import b64encode
from datetime import datetime

import pytz
# noinspection PyPackageRequirements
from google.cloud.storage import Client
# noinspection PyPackageRequirements
from googleapiclient.discovery import build


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or b64encode(os.urandom(24)).decode()
    CI_SECURITY = True if os.environ.get("ENVIRONMENT") == "prod" else False
    SESSION_COOKIE_SECURE = CI_SECURITY
    TOKEN_EXPIRY = 3600  # 1 hour = 3600 seconds
    SLIDES = build("slides", "v1")
    # noinspection SpellCheckingInspection
    CERTIFICATE_FILE_ID = "1KtZj6Vds3a1voBkx07eWHQpj9YH3mDAAAX0YjhfhTfw"
    DRIVE = build("drive", "v3")
    DOWNLOAD_PATH = os.path.join(os.path.abspath(os.sep), "tmp")
    CERTIFICATE_BUCKET = Client().bucket("hr-certificates")
    STORAGE_CLIENT = Client()


def today() -> datetime:
    now = datetime.now(tz=pytz.UTC)
    return datetime(year=now.year, month=now.month, day=now.day, tzinfo=pytz.UTC)
