from datetime import date

from flask import render_template
from flask_login import login_required

from extensions import db
from models import Book, Member, Transaction
from routes import dashboard_bp


@dashboard_bp.route("/")
@login_required
def index():
    total_copies = db.session.query(
        db.func.coalesce(db.func.sum(Book.total_copies), 0)
    ).scalar()
    total_books = Book.query.count()
    total_members = Member.query.count()
    issued = Transaction.query.filter_by(status="issued").count()
    returned = Transaction.query.filter_by(status="returned").count()
    overdue = Transaction.query.filter(
        Transaction.status == "issued", Transaction.due_date < date.today()
    ).count()

    recent_issues = Transaction.query.order_by(Transaction.id.desc()).limit(6).all()
    overdue_issues = (
        Transaction.query.filter(
            Transaction.status == "issued", Transaction.due_date < date.today()
        )
        .order_by(Transaction.due_date.asc())
        .limit(6)
        .all()
    )
    low_stock_books = (
        Book.query.filter(Book.available_copies < 2)
        .order_by(Book.available_copies.asc())
        .limit(6)
        .all()
    )

    return render_template(
        "dashboard.html",
        stats={
            "total_books": total_books,
            "total_copies": total_copies,
            "total_members": total_members,
            "issued": issued,
            "returned": returned,
            "overdue": overdue,
        },
        recent_issues=recent_issues,
        overdue_issues=overdue_issues,
        low_stock_books=low_stock_books,
    )