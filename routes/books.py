import re

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from extensions import db
from models import Book, Transaction
from routes import books_bp
import supabase_client


def _search_query(q):
    term = f"%{q}%"
    if q:
        digits = re.sub(r"[^0-9]", "", q)
        if digits:
            return Book.query.filter(
                or_(
                    Book.id == int(digits),
                    Book.book_id.ilike(term),
                    Book.title.ilike(term),
                    Book.author.ilike(term),
                    Book.category.ilike(term),
                )
            )
        return Book.query.filter(
            or_(
                Book.book_id.ilike(term),
                Book.title.ilike(term),
                Book.author.ilike(term),
                Book.category.ilike(term),
            )
        )
    return Book.query


@books_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    pagination = _search_query(q).order_by(Book.title.asc(), Book.id.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template(
        "books/list.html", pagination=pagination, books=pagination.items, q=q
    )


@books_bp.route("/<int:book_id>")
@login_required
def view(book_id):
    book = db.get_or_404(Book, book_id)
    history = (
        Transaction.query.filter_by(book_id=book.id)
        .order_by(Transaction.id.desc())
        .all()
    )
    return render_template("books/view.html", book=book, history=history)


@books_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = _parse_form()
        error = _validate(data)
        if error:
            flash(error, "error")
            return render_template("books/form.html", book=data, editing=False), 400

        book = Book(**data)
        db.session.add(book)
        db.session.commit()
        supabase_client.sync_book(book)
        flash(f'Book "{book.title}" added successfully.', "success")
        return redirect(url_for("books.view", book_id=book.id))

    return render_template("books/form.html", book={}, editing=False)


@books_bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit(book_id):
    book = db.get_or_404(Book, book_id)
    if request.method == "POST":
        data = _parse_form()
        error = _validate(data, editing_id=book_id)
        if error:
            flash(error, "error")
            return render_template(
                "books/form.html", book=data, editing=True, book_id=book.id
            ), 400

        delta = book.total_copies - data["total_copies"]
        book.book_id = data["book_id"]
        book.title = data["title"]
        book.author = data["author"]
        book.category = data["category"]
        book.publisher = data["publisher"]
        book.published_year = data["published_year"]
        book.description = data["description"]
        book.total_copies = data["total_copies"]
        book.available_copies = max(book.available_copies - delta, 0)
        db.session.commit()
        supabase_client.sync_book(book)
        flash(f'Book "{book.title}" updated successfully.', "success")
        return redirect(url_for("books.view", book_id=book.id))

    return render_template("books/form.html", book=book, editing=True, book_id=book.id)


@books_bp.route("/<int:book_id>/delete", methods=["POST"])
@login_required
def delete(book_id):
    book = db.get_or_404(Book, book_id)
    issued = book.issued_copies
    title = book.title
    db.session.delete(book)
    db.session.commit()
    supabase_client.delete_row("books", book.id)
    if issued:
        flash(
            f'Book "{title}" deleted. Its {issued} issued copy/copies and lending records were removed too.',
            "warning",
        )
    else:
        flash(f'Book "{title}" deleted successfully.', "success")
    return redirect(url_for("books.index"))


def _parse_form():
    return {
        "book_id": request.form.get("book_id", "").strip(),
        "title": request.form.get("title", "").strip(),
        "author": request.form.get("author", "").strip(),
        "category": request.form.get("category", "").strip(),
        "publisher": request.form.get("publisher", "").strip(),
        "published_year": _to_int(request.form.get("published_year")),
        "total_copies": _to_int(request.form.get("total_copies"), default=1),
        "description": request.form.get("description", "").strip(),
    }


def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _validate(data, editing_id=None):
    if not data["book_id"]:
        return "Book ID is required."
    if len(data["book_id"]) > 50 or not re.fullmatch(r"[A-Za-z0-9\-_./]+", data["book_id"]):
        return 'Book ID may only contain letters, numbers, dashes, underscores, dots, and slashes (e.g. "505-303").'
    existing = Book.query.filter(Book.book_id == data["book_id"]).first()
    if existing and existing.id != editing_id:
        return f'Book ID "{data["book_id"]}" is already in use. Book IDs must be unique.'
    if not data["title"] or not data["author"]:
        return "Title and author are required."
    if data["total_copies"] is None or data["total_copies"] < 1:
        return "Total copies must be at least 1."
    if data["published_year"] is not None and not (
        1000 <= data["published_year"] <= 2100
    ):
        return "Published year must be between 1000 and 2100."
    return None