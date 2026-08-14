from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/")
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")
books_bp = Blueprint("books", __name__, url_prefix="/books")
members_bp = Blueprint("members", __name__, url_prefix="/members")
transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")

from routes import auth, books, dashboard, members, transactions  # noqa: E402,F401