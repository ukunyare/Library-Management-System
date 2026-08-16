from datetime import date, timedelta

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from models import Book, Member, Transaction
from routes import transactions_bp
import supabase_client


@transactions_bp.route("/")
@login_required
def index():
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    query = Transaction.query
    if status in ("issued", "returned"):
        query = query.filter_by(status=status)
    pagination = (
        query.join(Book)
        .order_by(Book.title.asc(), Transaction.id.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    return render_template(
        "transactions/list.html",
        pagination=pagination,
        transactions=pagination.items,
        status=status,
    )


@transactions_bp.route("/overdue")
@login_required
def overdue():
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "due")
    sort_dir = request.args.get("dir", "asc")
    if sort not in ("due", "issue"):
        sort = "due"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "asc"

    query = Transaction.query.filter(
        Transaction.status == "issued", Transaction.due_date < date.today()
    )

    def _date_param(name):
        try:
            return date.fromisoformat(request.args.get(name, ""))
        except (TypeError, ValueError):
            return None

    issued_from = _date_param("issued_from")
    issued_to = _date_param("issued_to")
    due_from = _date_param("due_from")
    due_to = _date_param("due_to")
    if issued_from:
        query = query.filter(Transaction.issue_date >= issued_from)
    if issued_to:
        query = query.filter(Transaction.issue_date <= issued_to)
    if due_from:
        query = query.filter(Transaction.due_date >= due_from)
    if due_to:
        query = query.filter(Transaction.due_date <= due_to)

    column = Transaction.due_date if sort == "due" else Transaction.issue_date
    query = query.order_by(column.asc() if sort_dir == "asc" else column.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    return render_template(
        "transactions/overdue.html",
        pagination=pagination,
        transactions=pagination.items,
        fine_per_day=current_app.config["FINE_PER_DAY"],
        sort=sort,
        sort_dir=sort_dir,
    )


@transactions_bp.route("/test-overdue", methods=["POST"])
@login_required
def test_overdue():
    """Admin testing/demo helper: create a real overdue transaction.

    Uses past dates (issued 21 days ago, due 10 days ago) so it shows up on
    the Overdue page immediately. Stored exactly like any normal transaction.
    """
    book = (
        Book.query.filter(Book.available_copies > 0)
        .order_by(Book.title.asc())
        .first()
    )
    member = Member.query.order_by(Member.name.asc()).first()
    if book is None:
        flash(
            "No book with available copies — cannot create a test overdue transaction.",
            "error",
        )
        return redirect(url_for("transactions.overdue"))
    if member is None:
        flash("No member registered — cannot create a test overdue transaction.", "error")
        return redirect(url_for("transactions.overdue"))

    issue_date = date.today() - timedelta(days=21)
    due_date = date.today() - timedelta(days=10)
    tx = Transaction(
        book=book,
        member=member,
        issue_date=issue_date,
        due_date=due_date,
        status="issued",
    )
    book.available_copies -= 1
    db.session.add(tx)
    db.session.commit()
    supabase_client.sync_book(book)
    supabase_client.sync_transaction(tx)

    overdue_days = tx.days_overdue()
    fine = overdue_days * current_app.config["FINE_PER_DAY"]
    flash(
        f"Test overdue transaction created: \"{book.title}\" issued to "
        f"{member.name} on {issue_date:%b %d, %Y}, due {due_date:%b %d, %Y} "
        f"({overdue_days} day(s) overdue, projected fine ${fine:.2f}).",
        "success",
    )
    return redirect(url_for("transactions.overdue"))


@transactions_bp.route("/issue", methods=["GET", "POST"])
@login_required
def issue():
    if request.method == "POST":
        book_id = _to_int(request.form.get("book_id"))
        member_id = _to_int(request.form.get("member_id"))
        due_date = _parse_date(request.form.get("due_date"))
        book = db.session.get(Book, book_id) if book_id else None
        member = db.session.get(Member, member_id) if member_id else None

        error = _validate_issue(book, member, due_date)
        if error:
            flash(error, "error")
            return _render_issue_form(book_id, member_id, due_date), 400

        tx = Transaction(
            book=book,
            member=member,
            issue_date=date.today(),
            due_date=due_date,
            status="issued",
        )
        book.available_copies -= 1
        db.session.add(tx)
        db.session.commit()
        supabase_client.sync_book(book)
        supabase_client.sync_transaction(tx)
        flash(
            f'Book "{book.title}" issued to {member.name} until {due_date:%Y-%m-%d}.',
            "success",
        )
        return redirect(url_for("transactions.index"))

    return _render_issue_form()


def _render_issue_form(book_id=None, member_id=None, due_date=None):
    books = (
        Book.query.filter(Book.available_copies > 0)
        .order_by(Book.title.asc())
        .all()
    )
    members = Member.query.order_by(Member.name.asc()).all()
    default_due = date.today() + timedelta(days=current_app.config["ISSUE_DAYS"])
    return render_template(
        "transactions/issue.html",
        books=books,
        members=members,
        selected_book=book_id,
        selected_member=member_id,
        due_date=due_date or default_due,
        default_days=current_app.config["ISSUE_DAYS"],
    )


def _validate_issue(book, member, due_date):
    if book is None or member is None:
        return "Please select both a book and a member."
    if book.available_copies < 1:
        return f'"{book.title}" has no available copies right now.'
    if due_date is None:
        return "Due date is required."
    if due_date <= date.today():
        return "Due date must be after today."
    return None


@transactions_bp.route("/<int:tx_id>/edit-dates", methods=["POST"])
@login_required
def edit_dates(tx_id):
    tx = db.get_or_404(Transaction, tx_id)
    if tx.status != "issued":
        flash("Only issued transactions can have their dates edited.", "error")
        return redirect(request.referrer or url_for("transactions.index"))

    issue_date = _parse_date(request.form.get("issue_date"))
    due_date = _parse_date(request.form.get("due_date"))
    if issue_date is None or due_date is None:
        flash("Both Issued and Due dates are required.", "error")
        return redirect(request.referrer or url_for("transactions.overdue"))
    if due_date < issue_date:
        flash("Due date cannot be before the issued date.", "error")
        return redirect(request.referrer or url_for("transactions.overdue"))

    tx.issue_date = issue_date
    tx.due_date = due_date
    db.session.commit()
    supabase_client.sync_transaction(tx)
    flash(
        f'Dates updated for "{tx.book.title}": '
        f"issued {issue_date:%b %d, %Y}, due {due_date:%b %d, %Y}.",
        "success",
    )
    return redirect(request.referrer or url_for("transactions.overdue"))


@transactions_bp.route("/<int:tx_id>/return", methods=["POST"])
@login_required
def return_book(tx_id):
    tx = db.get_or_404(Transaction, tx_id)
    if tx.status != "issued":
        flash("This transaction is already returned.", "error")
        return redirect(url_for("transactions.index"))

    overdue_days = tx.days_overdue()
    fine = round(overdue_days * current_app.config["FINE_PER_DAY"], 2)
    tx.returned_at = date.today()
    tx.status = "returned"
    tx.fine = fine
    tx.book.available_copies += 1
    db.session.commit()
    supabase_client.sync_transaction(tx)
    supabase_client.sync_book(tx.book)

    if fine:
        flash(
            f'"{tx.book.title}" returned after {overdue_days} overdue day(s) '
            f"with a fine of ${fine:.2f}.",
            "warning",
        )
    else:
        flash(f'"{tx.book.title}" returned successfully.', "success")
    return redirect(request.referrer or url_for("transactions.index"))


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None