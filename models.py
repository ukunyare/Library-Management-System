from datetime import date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(80))
    publisher = db.Column(db.String(120))
    published_year = db.Column(db.Integer)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    transactions = db.relationship(
        "Transaction", backref="book", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def issued_copies(self):
        return self.total_copies - self.available_copies

    def __repr__(self):
        return f"<Book {self.title}>"


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    phone = db.Column(db.String(20), index=True)
    address = db.Column(db.String(255))
    joined_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=db.func.now())

    transactions = db.relationship(
        "Transaction", backref="member", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def active_issue_count(self):
        return self.transactions.filter_by(status="issued").count()

    def __repr__(self):
        return f"<Member {self.name}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(
        db.Integer, db.ForeignKey("books.id"), nullable=False, index=True
    )
    member_id = db.Column(
        db.Integer, db.ForeignKey("members.id"), nullable=False, index=True
    )
    issue_date = db.Column(db.Date, default=date.today, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    returned_at = db.Column(db.Date)
    fine = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="issued", index=True)  # issued | returned

    def days_overdue(self, today=None):
        today = today or date.today()
        if self.returned_at:
            return max((self.returned_at - self.due_date).days, 0)
        return max((today - self.due_date).days, 0)

    @property
    def is_overdue(self):
        return self.returned_at is None and self.due_date < date.today()

    @property
    def overdue_days(self):
        return self.days_overdue()

    def __repr__(self):
        return f"<Transaction {self.id} book={self.book_id} member={self.member_id}>"
