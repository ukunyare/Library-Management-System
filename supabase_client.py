import json
import os
import urllib.error
import urllib.request

from config import Config

_BASE = os.environ.get("SUPABASE_URL", "").rstrip("/")
_KEY = os.environ.get("SUPABASE_KEY", "")
_uri = Config.SQLALCHEMY_DATABASE_URI

ENABLED = (
    os.environ.get("USE_SUPABASE", "").lower() == "true"
    and bool(_BASE)
    and bool(_KEY)
    and _uri.startswith("sqlite:///")
    and "lms_test" not in _uri
)

_HEADERS = {
    "apikey": _KEY,
    "Authorization": f"Bearer {_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def _request(method, path, payload=None, prefer=None):
    if not ENABLED:
        return None
    headers = dict(_HEADERS)
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(_BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read()[:200]
        print(f"[supabase] {method} {path} -> {exc.code}: {body}")
        return None
    except Exception as exc:
        print(f"[supabase] {method} {path} -> {exc}")
        return None


def book_dict(book):
    return {
        "id": book.id,
        "book_id": book.book_id,
        "title": book.title,
        "author": book.author,
        "category": book.category,
        "publisher": book.publisher,
        "published_year": book.published_year,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
        "description": book.description,
    }


def member_dict(member):
    return {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "phone": member.phone,
        "address": member.address,
    }


def tx_dict(tx):
    return {
        "id": tx.id,
        "book_id": tx.book_id,
        "member_id": tx.member_id,
        "issue_date": tx.issue_date.isoformat() if tx.issue_date else None,
        "due_date": tx.due_date.isoformat() if tx.due_date else None,
        "returned_at": tx.returned_at.isoformat() if tx.returned_at else None,
        "fine": tx.fine,
        "status": tx.status,
    }


def upsert(table, payloads):
    if not ENABLED or not payloads:
        return
    for payload in payloads:
        _request(
            "POST",
            f"/rest/v1/{table}?on_conflict=id",
            payload,
            prefer="resolution=merge-duplicates",
        )


def delete_row(table, row_id):
    _request("DELETE", f"/rest/v1/{table}?id=eq.{row_id}")


def sync_book(book):
    upsert("books", [book_dict(book)])


def sync_member(member):
    upsert("members", [member_dict(member)])


def sync_transaction(tx):
    upsert("transactions", [tx_dict(tx)])


def _get(table, select="*"):
    if not ENABLED:
        return []
    req = urllib.request.Request(
        _BASE + f"/rest/v1/{table}?select={select}", headers=_HEADERS, method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        print(f"[supabase] GET {table} -> {exc}")
        return []


def seed():
    if not ENABLED:
        return
    from extensions import db
    from models import Admin, Book, Member, Transaction

    if Book.query.count() == 0:
        rows = _get("books")
        if rows:
            for row in rows:
                db.session.add(
                    Book(
                        id=row.get("id"),
                        book_id=row["book_id"],
                        title=row["title"],
                        author=row["author"],
                        category=row.get("category"),
                        publisher=row.get("publisher"),
                        published_year=row.get("published_year"),
                        total_copies=row.get("total_copies", 1),
                        available_copies=row.get("available_copies", 1),
                        description=row.get("description"),
                    )
                )
            db.session.commit()
            print(f"[supabase] pulled {len(rows)} books from Supabase")
    if Member.query.count() == 0:
        rows = _get("members")
        if rows:
            for row in rows:
                db.session.add(
                    Member(
                        id=row.get("id"),
                        name=row["name"],
                        email=row.get("email"),
                        phone=row.get("phone"),
                        address=row.get("address"),
                    )
                )
            db.session.commit()
            print(f"[supabase] pulled {len(rows)} members from Supabase")
    if Transaction.query.count() == 0:
        rows = _get("transactions")
        if rows:
            for row in rows:
                db.session.add(
                    Transaction(
                        id=row.get("id"),
                        book_id=row["book_id"],
                        member_id=row["member_id"],
                        issue_date=row["issue_date"],
                        due_date=row["due_date"],
                        returned_at=row.get("returned_at"),
                        fine=row.get("fine", 0),
                        status=row.get("status", "issued"),
                    )
                )
            db.session.commit()
            print(f"[supabase] pulled {len(rows)} transactions from Supabase")

    upsert("books", [book_dict(b) for b in Book.query.all()])
    upsert("members", [member_dict(m) for m in Member.query.all()])
    upsert("transactions", [tx_dict(t) for t in Transaction.query.all()])
    upsert(
        "admins",
        [
            {"id": a.id, "username": a.username, "password_hash": a.password_hash}
            for a in Admin.query.all()
        ],
    )
    print("[supabase] sync complete")
