from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models import Admin
from routes import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        error = None
        if not username or not password:
            error = "Username and password are required."
        else:
            admin = Admin.query.filter_by(username=username).first()
            if admin is None or not admin.check_password(password):
                error = "Invalid username or password."

        if error:
            flash(error, "error")
            return render_template("login.html"), 401

        login_user(admin, remember=request.form.get("remember") == "on")
        flash(f"Welcome back, {admin.username}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))