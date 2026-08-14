from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    from models import Admin

    return Admin.query.get(int(user_id))
