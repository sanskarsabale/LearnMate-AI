"""
============================================================
Admin Routes — Admin Dashboard
============================================================
Admin-only views: student management, resource management,
progress monitoring, export reports.
============================================================
"""

import csv
import io
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify, make_response,
)
from flask_login import login_required, current_user
from functools import wraps
from models import db, Student, SkillAssessment, LearningRoadmap, Progress, Resource

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    """Decorator: restrict route to admin users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Administrator access required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── Admin Dashboard ───────────────────────────────────────────
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_students  = Student.query.filter_by(is_admin=False).count()
    active_students = Student.query.filter_by(is_admin=False, is_active=True).count()
    assessments     = SkillAssessment.query.count()
    roadmaps        = LearningRoadmap.query.count()
    total_resources = Resource.query.count()

    recent_students = (
        Student.query.filter_by(is_admin=False)
        .order_by(Student.created_at.desc())
        .limit(10).all()
    )

    # Level distribution
    level_data = db.session.execute(
        db.select(SkillAssessment.level, db.func.count(SkillAssessment.id))
        .group_by(SkillAssessment.level)
    ).fetchall()

    # Domain distribution
    domain_data = db.session.execute(
        db.select(Student.preferred_domain, db.func.count(Student.id))
        .where(Student.preferred_domain.isnot(None))
        .group_by(Student.preferred_domain)
    ).fetchall()

    return render_template(
        "admin/dashboard.html",
        total_students  = total_students,
        active_students = active_students,
        assessments     = assessments,
        roadmaps        = roadmaps,
        total_resources = total_resources,
        recent_students = recent_students,
        level_data      = dict(level_data),
        domain_data     = dict(domain_data),
    )


# ── Student Management ────────────────────────────────────────
@admin_bp.route("/students")
@login_required
@admin_required
def students():
    page    = request.args.get("page", 1, type=int)
    search  = request.args.get("search", "")
    query   = Student.query.filter_by(is_admin=False)
    if search:
        query = query.filter(
            Student.name.ilike(f"%{search}%") |
            Student.email.ilike(f"%{search}%") |
            Student.preferred_domain.ilike(f"%{search}%")
        )
    students_page = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/students.html", students=students_page, search=search)


@admin_bp.route("/students/<int:student_id>")
@login_required
@admin_required
def student_detail(student_id):
    student     = Student.query.get_or_404(student_id)
    assessments = student.assessments.order_by(SkillAssessment.created_at.desc()).all()
    roadmaps    = student.roadmaps.order_by(LearningRoadmap.created_at.desc()).all()
    progress    = student.progress_records.order_by(Progress.logged_at.desc()).all()
    return render_template(
        "admin/student_detail.html",
        student=student, assessments=assessments,
        roadmaps=roadmaps, progress=progress,
    )


@admin_bp.route("/students/<int:student_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_active = not student.is_active
    db.session.commit()
    status = "activated" if student.is_active else "deactivated"
    return jsonify({"success": True, "status": status, "is_active": student.is_active})


# ── Resource Management ───────────────────────────────────────
@admin_bp.route("/resources")
@login_required
@admin_required
def resources():
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template("admin/resources.html", resources=resources)


@admin_bp.route("/resources/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_resource():
    if request.method == "POST":
        resource = Resource(
            title         = request.form.get("title", ""),
            url           = request.form.get("url", ""),
            platform      = request.form.get("platform", ""),
            resource_type = request.form.get("resource_type", "course"),
            domain        = request.form.get("domain", ""),
            level         = request.form.get("level", "Beginner"),
            description   = request.form.get("description", ""),
            is_free       = request.form.get("is_free") == "on",
            rating        = float(request.form.get("rating", 0) or 0),
            tags          = request.form.get("tags", ""),
        )
        db.session.add(resource)
        db.session.commit()
        flash("Resource added successfully! ✅", "success")
        return redirect(url_for("admin.resources"))
    return render_template("admin/add_resource.html")


@admin_bp.route("/resources/<int:resource_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    db.session.delete(resource)
    db.session.commit()
    return jsonify({"success": True})


# ── Export Reports ────────────────────────────────────────────
@admin_bp.route("/export/students")
@login_required
@admin_required
def export_students():
    students = Student.query.filter_by(is_admin=False).all()
    output   = io.StringIO()
    writer   = csv.writer(output)
    writer.writerow([
        "ID", "Name", "Email", "Branch", "Semester", "College",
        "Career Goal", "Domain", "Learning Style", "Weekly Hours",
        "Profile Complete", "Active", "Joined",
    ])
    for s in students:
        writer.writerow([
            s.id, s.name, s.email, s.branch, s.semester, s.college,
            s.career_goal, s.preferred_domain, s.learning_style,
            s.weekly_hours, s.profile_complete, s.is_active,
            s.created_at.strftime("%Y-%m-%d") if s.created_at else "",
        ])
    resp = make_response(output.getvalue())
    resp.headers["Content-Disposition"] = "attachment; filename=learnmate_students.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
