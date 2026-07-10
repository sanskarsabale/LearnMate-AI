"""
============================================================
Dashboard & Main App Routes
============================================================
All student-facing pages: dashboard, profile, assessment,
roadmap, resources, career, projects, progress, chat, settings.
============================================================
"""

import json
from datetime import datetime, date
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify,
)
from flask_login import login_required, current_user
from models import (
    db, Student, SkillAssessment, LearningRoadmap,
    Progress, Resource, CareerGoal, RecommendedProject, DailyTask,
)

dashboard_bp = Blueprint("dashboard", __name__)


# ── Landing page ──────────────────────────────────────────────
@dashboard_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")


# ── Student Dashboard ─────────────────────────────────────────
@dashboard_bp.route("/dashboard")
@login_required
def index():
    # Redirect to profile completion if needed
    if not current_user.profile_complete:
        return redirect(url_for("dashboard.complete_profile"))

    # Gather dashboard data
    latest_assessment = (
        SkillAssessment.query
        .filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc())
        .first()
    )
    active_roadmap = (
        LearningRoadmap.query
        .filter_by(student_id=current_user.id, is_active=True)
        .first()
    )
    progress_records = (
        Progress.query
        .filter_by(student_id=current_user.id)
        .order_by(Progress.logged_at.desc())
        .limit(8)
        .all()
    )
    today_tasks = (
        DailyTask.query
        .filter_by(student_id=current_user.id, task_date=date.today())
        .order_by(DailyTask.priority)
        .all()
    )
    recent_projects = (
        RecommendedProject.query
        .filter_by(student_id=current_user.id)
        .order_by(RecommendedProject.created_at.desc())
        .limit(3)
        .all()
    )

    # Progress metrics
    total_weeks      = active_roadmap.duration_weeks if active_roadmap else 12
    completed_weeks  = len(progress_records)
    completion_pct   = round((completed_weeks / total_weeks) * 100, 1) if total_weeks else 0
    streak           = _calculate_streak(progress_records)
    total_hours      = sum(p.total_hours_spent or 0 for p in progress_records)

    # Weekly chart data (last 8 weeks)
    chart_data = {
        "labels": [f"Wk {p.week_number or (i+1)}" for i, p in enumerate(reversed(progress_records))],
        "hours":  [p.total_hours_spent or 0 for p in reversed(progress_records)],
        "pct":    [p.completion_pct or 0 for p in reversed(progress_records)],
    }

    return render_template(
        "dashboard/index.html",
        assessment       = latest_assessment,
        roadmap          = active_roadmap,
        today_tasks      = today_tasks,
        recent_projects  = recent_projects,
        completion_pct   = completion_pct,
        streak           = streak,
        total_hours      = round(total_hours, 1),
        completed_weeks  = completed_weeks,
        total_weeks      = total_weeks,
        chart_data       = json.dumps(chart_data),
    )


# ── Profile Setup ─────────────────────────────────────────────
@dashboard_bp.route("/profile/setup", methods=["GET", "POST"])
@login_required
def complete_profile():
    if request.method == "POST":
        current_user.branch          = request.form.get("branch", "")
        current_user.semester        = int(request.form.get("semester", 1) or 1)
        current_user.college         = request.form.get("college", "")
        current_user.career_goal     = request.form.get("career_goal", "")
        current_user.preferred_domain = request.form.get("preferred_domain", "")
        current_user.learning_style  = request.form.get("learning_style", "visual")
        current_user.weekly_hours    = int(request.form.get("weekly_hours", 10) or 10)
        current_user.current_skills  = request.form.get("current_skills", "")
        current_user.bio             = request.form.get("bio", "")
        current_user.profile_complete = True
        db.session.commit()

        # Run Profile Agent analysis
        try:
            from agents import StudentProfileAgent
            agent   = StudentProfileAgent()
            summary = agent.analyse_profile({
                "name":             current_user.name,
                "branch":           current_user.branch,
                "semester":         current_user.semester,
                "career_goal":      current_user.career_goal,
                "preferred_domain": current_user.preferred_domain,
                "learning_style":   current_user.learning_style,
                "weekly_hours":     current_user.weekly_hours,
                "current_skills":   current_user.current_skills,
                "bio":              current_user.bio,
            })
            flash(summary, "ai_message")
        except Exception:
            flash(f"Profile saved! Welcome, {current_user.name}! 🚀", "success")

        return redirect(url_for("dashboard.skill_assessment"))

    return render_template("dashboard/profile_setup.html")


@dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name            = request.form.get("name", current_user.name)
        current_user.branch          = request.form.get("branch", "")
        current_user.semester        = int(request.form.get("semester", 1) or 1)
        current_user.college         = request.form.get("college", "")
        current_user.career_goal     = request.form.get("career_goal", "")
        current_user.preferred_domain = request.form.get("preferred_domain", "")
        current_user.learning_style  = request.form.get("learning_style", "visual")
        current_user.weekly_hours    = int(request.form.get("weekly_hours", 10) or 10)
        current_user.current_skills  = request.form.get("current_skills", "")
        current_user.bio             = request.form.get("bio", "")
        db.session.commit()
        flash("Profile updated successfully! ✅", "success")
    return render_template("dashboard/profile.html")


# ── Skill Assessment ──────────────────────────────────────────
@dashboard_bp.route("/assessment")
@login_required
def skill_assessment():
    past_assessments = (
        SkillAssessment.query
        .filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template("dashboard/assessment.html", past_assessments=past_assessments)


# ── Learning Roadmap ──────────────────────────────────────────
@dashboard_bp.route("/roadmap")
@login_required
def roadmap():
    active_roadmap = (
        LearningRoadmap.query
        .filter_by(student_id=current_user.id, is_active=True)
        .first()
    )
    roadmap_data = None
    if active_roadmap:
        try:
            roadmap_data = json.loads(active_roadmap.roadmap_json)
        except Exception:
            roadmap_data = None

    return render_template(
        "dashboard/roadmap.html",
        roadmap       = active_roadmap,
        roadmap_data  = roadmap_data,
    )


# ── Resources ─────────────────────────────────────────────────
@dashboard_bp.route("/resources")
@login_required
def resources():
    domain    = request.args.get("domain", current_user.preferred_domain or "")
    level     = request.args.get("level", "")
    platform  = request.args.get("platform", "")
    query     = Resource.query.filter_by(is_active=True)
    if domain:
        query = query.filter(Resource.domain.contains(domain))
    if level:
        query = query.filter_by(level=level)
    if platform:
        query = query.filter_by(platform=platform)
    db_resources = query.order_by(Resource.rating.desc()).all()
    platforms = db.session.query(Resource.platform).distinct().all()
    platforms = [p[0] for p in platforms]
    return render_template(
        "dashboard/resources.html",
        resources  = db_resources,
        platforms  = platforms,
        domain     = domain,
        level      = level,
        platform   = platform,
    )


# ── Career Guidance ───────────────────────────────────────────
@dashboard_bp.route("/career")
@login_required
def career():
    career_plan = (
        CareerGoal.query
        .filter_by(student_id=current_user.id)
        .order_by(CareerGoal.created_at.desc())
        .first()
    )
    plan_data = None
    if career_plan and career_plan.ai_guidance:
        try:
            plan_data = json.loads(career_plan.ai_guidance)
        except Exception:
            plan_data = None
    return render_template("dashboard/career.html", career_plan=career_plan, plan_data=plan_data)


# ── Projects ──────────────────────────────────────────────────
@dashboard_bp.route("/projects")
@login_required
def projects():
    all_projects = (
        RecommendedProject.query
        .filter_by(student_id=current_user.id)
        .order_by(RecommendedProject.created_at.desc())
        .all()
    )
    beginner     = [p for p in all_projects if p.difficulty == "Beginner"]
    intermediate = [p for p in all_projects if p.difficulty == "Intermediate"]
    advanced     = [p for p in all_projects if p.difficulty == "Advanced"]
    return render_template(
        "dashboard/projects.html",
        beginner=beginner, intermediate=intermediate, advanced=advanced,
        total=len(all_projects),
    )


@dashboard_bp.route("/projects/<int:project_id>/complete", methods=["POST"])
@login_required
def complete_project(project_id):
    project = RecommendedProject.query.filter_by(
        id=project_id, student_id=current_user.id
    ).first_or_404()
    project.is_completed = True
    db.session.commit()
    return jsonify({"success": True})


# ── Progress Tracker ──────────────────────────────────────────
@dashboard_bp.route("/progress")
@login_required
def progress():
    all_progress = (
        Progress.query
        .filter_by(student_id=current_user.id)
        .order_by(Progress.logged_at.desc())
        .all()
    )
    active_roadmap = (
        LearningRoadmap.query
        .filter_by(student_id=current_user.id, is_active=True)
        .first()
    )

    from agents import ProgressTrackingAgent
    agent = ProgressTrackingAgent()
    progress_dicts = [
        {
            "week_number":      p.week_number,
            "completion_pct":   p.completion_pct,
            "total_hours_spent":p.total_hours_spent,
            "skills_gained":    p.skills_gained,
            "logged_at":        p.logged_at,
        }
        for p in all_progress
    ]
    roadmap_dict = {}
    if active_roadmap:
        roadmap_dict = {"duration_weeks": active_roadmap.duration_weeks}

    metrics     = agent.calculate_metrics(progress_dicts, roadmap_dict)
    chart_data  = json.dumps({
        "labels": [f"Week {p.week_number or i+1}" for i, p in enumerate(reversed(all_progress))],
        "hours":  [p.total_hours_spent or 0 for p in reversed(all_progress)],
        "pct":    [p.completion_pct or 0 for p in reversed(all_progress)],
    })

    return render_template(
        "dashboard/progress.html",
        progress_records = all_progress,
        metrics          = metrics,
        chart_data       = chart_data,
    )


@dashboard_bp.route("/progress/log", methods=["POST"])
@login_required
def log_progress():
    week        = request.form.get("week_number", 1)
    hours       = float(request.form.get("hours_spent", 0) or 0)
    skills      = request.form.get("skills_gained", "")
    modules     = request.form.get("completed_modules", "")
    notes       = request.form.get("notes", "")

    active_roadmap = LearningRoadmap.query.filter_by(
        student_id=current_user.id, is_active=True
    ).first()
    total_weeks    = active_roadmap.duration_weeks if active_roadmap else 12
    comp_pct       = round((int(week) / total_weeks) * 100, 1)

    record = Progress(
        student_id         = current_user.id,
        roadmap_id         = active_roadmap.id if active_roadmap else None,
        week_number        = int(week),
        completed_modules  = json.dumps([m.strip() for m in modules.split(",") if m.strip()]),
        completion_pct     = comp_pct,
        total_hours_spent  = hours,
        skills_gained      = json.dumps([s.strip() for s in skills.split(",") if s.strip()]),
        notes              = notes,
    )
    db.session.add(record)
    db.session.commit()
    flash("Progress logged successfully! Keep it up! 🎯", "success")
    return redirect(url_for("dashboard.progress"))


# ── AI Mentor Chat ────────────────────────────────────────────
@dashboard_bp.route("/chat")
@login_required
def chat():
    from models import ChatMessage
    recent_messages = (
        ChatMessage.query
        .filter_by(student_id=current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(50)
        .all()
    )
    return render_template("dashboard/chat.html", messages=recent_messages)


# ── Settings ──────────────────────────────────────────────────
@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change_password":
            current_pw  = request.form.get("current_password", "")
            new_pw      = request.form.get("new_password", "")
            confirm_pw  = request.form.get("confirm_password", "")
            if not current_user.check_password(current_pw):
                flash("Current password is incorrect.", "danger")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "danger")
            elif len(new_pw) < 8:
                flash("Password must be at least 8 characters.", "danger")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed successfully! 🔐", "success")
        elif action == "theme":
            theme = request.form.get("theme", "light")
            current_user.theme_preference = theme
            db.session.commit()
            return jsonify({"success": True, "theme": theme})
    return render_template("dashboard/settings.html")


# ── Helper ────────────────────────────────────────────────────
def _calculate_streak(progress_records) -> int:
    if not progress_records:
        return 0
    dates = sorted(
        set(p.logged_at.date() for p in progress_records if p.logged_at),
        reverse=True,
    )
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak
