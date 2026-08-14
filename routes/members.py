from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from extensions import db
from models import Member, Transaction
from routes import members_bp
import supabase_client


def _search_query(q):
    term = f"%{q}%"
    query = Member.query
    if q:
        query = query.filter(
            or_(
                Member.name.ilike(term),
                Member.email.ilike(term),
                Member.phone.ilike(term),
            )
        )
    return query


@members_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    pagination = _search_query(q).order_by(Member.name.asc(), Member.id.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template(
        "members/list.html", pagination=pagination, members=pagination.items, q=q
    )


@members_bp.route("/<int:member_id>")
@login_required
def view(member_id):
    member = db.get_or_404(Member, member_id)
    active = (
        Transaction.query.filter_by(member_id=member.id, status="issued")
        .order_by(Transaction.due_date.asc())
        .all()
    )
    history = (
        Transaction.query.filter_by(member_id=member.id, status="returned")
        .order_by(Transaction.returned_at.desc())
        .all()
    )
    return render_template(
        "members/view.html", member=member, active=active, history=history
    )


@members_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        data = _parse_form()
        error = _validate(data)
        if error:
            flash(error, "error")
            return render_template("members/form.html", member=data, editing=False), 400

        member = Member(**data)
        db.session.add(member)
        db.session.commit()
        supabase_client.sync_member(member)
        flash(f'Member "{member.name}" added successfully.', "success")
        return redirect(url_for("members.view", member_id=member.id))

    return render_template("members/form.html", member={}, editing=False)


@members_bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
def edit(member_id):
    member = db.get_or_404(Member, member_id)
    if request.method == "POST":
        data = _parse_form()
        error = _validate(data, editing_id=member.id)
        if error:
            flash(error, "error")
            return render_template(
                "members/form.html", member=data, editing=True, member_id=member.id
            ), 400

        member.name = data["name"]
        member.email = data["email"]
        member.phone = data["phone"]
        member.address = data["address"]
        db.session.commit()
        supabase_client.sync_member(member)
        flash(f'Member "{member.name}" updated successfully.', "success")
        return redirect(url_for("members.view", member_id=member.id))

    return render_template(
        "members/form.html", member=member, editing=True, member_id=member.id
    )


@members_bp.route("/<int:member_id>/delete", methods=["POST"])
@login_required
def delete(member_id):
    member = db.get_or_404(Member, member_id)
    active = member.transactions.filter_by(status="issued").all()
    issued_count = len(active)
    for tx in active:
        tx.book.available_copies += 1
    name = member.name
    db.session.delete(member)
    db.session.commit()
    supabase_client.delete_row("members", member.id)
    if issued_count:
        flash(
            f'Member "{name}" deleted. Their {issued_count} borrowed book(s) were returned and lending records removed.',
            "warning",
        )
    else:
        flash(f'Member "{name}" deleted successfully.', "success")
    return redirect(url_for("members.index"))


def _parse_form():
    return {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "address": request.form.get("address", "").strip(),
    }


def _validate(data, editing_id=None):
    if not data["name"]:
        return "Name is required."
    if data["email"]:
        existing = Member.query.filter(Member.email == data["email"]).first()
        if existing and existing.id != editing_id:
            return f'Email "{data["email"]}" is already registered.'
    if data["phone"] and not data["phone"].replace(" ", "").replace("-", "").isdigit():
        return "Phone number may only contain digits, spaces, and dashes."
    return None