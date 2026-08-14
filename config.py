import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "library-management-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "library.db"),
    )
    ISSUE_DAYS = int(os.environ.get("ISSUE_DAYS", "14"))
    FINE_PER_DAY = float(os.environ.get("FINE_PER_DAY", "1.0"))