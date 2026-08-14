import os
from datetime import date

from flask import Flask, render_template
from flask_login import current_user
from sqlalchemy import create_engine, text

from config import Config, BASE_DIR
from extensions import db, login_manager
from models import Admin, Transaction
from routes import auth_bp, books_bp, dashboard_bp, members_bp, transactions_bp
import supabase_client


def _db_reachable(uri, timeout=5):
    try:
        connect_args = {}
        if uri.startswith("postgresql"):
            connect_args = {"connect_timeout": timeout, "sslmode": "require"}
        engine = create_engine(uri, connect_args=connect_args)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as exc:
        print(f"[db] Could not connect to database: {exc}")
        return False


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not _db_reachable(app.config["SQLALCHEMY_DATABASE_URI"]):
        fallback = "sqlite:///" + os.path.join(BASE_DIR, "library.db")
        print(f"[db] Using local SQLite instead: {fallback}")
        app.config["SQLALCHEMY_DATABASE_URI"] = fallback

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(transactions_bp)

    with app.app_context():
        db.create_all()
        _migrate_book_id_column()
        _create_default_admin()
        supabase_client.seed()

    _register_template_helpers(app)
    _register_error_handlers(app)
    return app


def _migrate_book_id_column():
    """Add the user-managed `book_id` column to existing databases."""
    inspector = db.inspect(db.engine)
    if "books" not in inspector.get_table_names():
        return
    columns = [c["name"] for c in inspector.get_columns("books")]
    if "book_id" in columns:
        return
    db.session.execute(text("ALTER TABLE books ADD COLUMN book_id VARCHAR(50)"))
    rows = db.session.execute(text("SELECT id FROM books")).fetchall()
    for (book_id,) in rows:
        db.session.execute(
            text("UPDATE books SET book_id = :value WHERE id = :id"),
            {"value": f"B-{book_id:04d}", "id": book_id},
        )
    db.session.execute(
        text("CREATE UNIQUE INDEX IF NOT EXISTS uq_books_book_id ON books (book_id)")
    )
    db.session.commit()
    print("[migrate] Added 'book_id' column to existing books table.")


def _create_default_admin():
    if Admin.query.count() == 0:
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print(
            "[setup] Default admin created -> username: admin | password: admin123"
        )


def _register_template_helpers(app):
    @app.context_processor
    def inject_globals():
        overdue_count = (
            Transaction.query.filter(
                Transaction.status == "issued", Transaction.due_date < date.today()
            ).count()
            if current_user.is_authenticated
            else 0
        )
        return {"now": date.today, "overdue_count": overdue_count}

    @app.template_filter("currency")
    def currency(value):
        return f"${value:,.2f}"

    @app.template_filter("datefmt")
    def datefmt(value, fmt="%b %d, %Y"):
        return value.strftime(fmt) if value else "—"


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("errors/403.html"), 403


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
