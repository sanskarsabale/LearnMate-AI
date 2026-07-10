"""
============================================================
Auth Routes — Login, Registration, Logout
============================================================
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session,
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from models import db, Student

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = Student.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact admin.", "danger")
                return redirect(url_for("auth.login"))
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.name}! 🎉", "success")
            next_page = request.args.get("next")
            if user.is_admin:
                return redirect(next_page or url_for("admin.dashboard"))
            return redirect(next_page or url_for("dashboard.index"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # Validation
        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")

        if Student.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html")

        student = Student(name=name, email=email)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        login_user(student)
        flash(f"Welcome to LearnMate AI, {name}! Let's set up your profile. 🚀", "success")
        return redirect(url_for("dashboard.complete_profile"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out. See you soon! 👋", "info")
    return redirect(url_for("auth.login"))
