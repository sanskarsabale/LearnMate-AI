"""
============================================================
Agents API Routes — JSON endpoints consumed by the frontend
============================================================
All AI agent calls are routed through here.
Each endpoint validates the user is logged in, calls the
appropriate agent, persists results, and returns JSON.
============================================================
"""

import json
from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, SkillAssessment, LearningRoadmap, CareerGoal,
    RecommendedProject, DailyTask, ChatMessage,
)
from agents import (
    StudentProfileAgent, SkillAssessmentAgent, PersonalizedRoadmapAgent,
    LearningMentorAgent, ResourceRecommendationAgent, CareerGuidanceAgent,
    ProgressTrackingAgent, ProjectRecommendationAgent,
)

agents_bp = Blueprint("agents", __name__)


# ── Agent 1: Profile Analysis ─────────────────────────────────
@agents_bp.route("/profile/analyse", methods=["POST"])
@login_required
def analyse_profile():
    try:
        agent   = StudentProfileAgent()
        profile = {
            "name":             current_user.name,
            "branch":           current_user.branch,
            "semester":         current_user.semester,
            "career_goal":      current_user.career_goal,
            "preferred_domain": current_user.preferred_domain,
            "learning_style":   current_user.learning_style,
            "weekly_hours":     current_user.weekly_hours,
            "current_skills":   current_user.current_skills,
            "bio":              current_user.bio,
        }
        summary = agent.analyse_profile(profile)
        return jsonify({"success": True, "summary": summary})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 2: Assessment — Generate Questions ──────────────────
@agents_bp.route("/assessment/questions", methods=["POST"])
@login_required
def get_assessment_questions():
    data   = request.get_json() or {}
    domain = data.get("domain", current_user.preferred_domain or "Python Programming")
    count  = int(data.get("count", 10))
    try:
        agent     = SkillAssessmentAgent()
        questions = agent.generate_questions(domain, count=count)
        return jsonify({"success": True, "questions": questions, "domain": domain})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 2: Assessment — Submit & Evaluate ───────────────────
@agents_bp.route("/assessment/evaluate", methods=["POST"])
@login_required
def evaluate_assessment():
    data      = request.get_json() or {}
    domain    = data.get("domain", current_user.preferred_domain or "General")
    questions = data.get("questions", [])
    answers   = data.get("answers", {})

    try:
        agent  = SkillAssessmentAgent()
        result = agent.evaluate_answers(domain, questions, answers)

        # Persist to DB
        assessment = SkillAssessment(
            student_id    = current_user.id,
            domain        = domain,
            level         = result["level"],
            score         = result["percentage"],
            skill_gaps    = json.dumps([g["question"] for g in result["skill_gaps"]]),
            strengths     = json.dumps(result["strengths"]),
            questions_json = json.dumps(questions),
            answers_json  = json.dumps(answers),
            ai_feedback   = result["feedback"],
        )
        db.session.add(assessment)
        db.session.commit()

        return jsonify({"success": True, "result": result, "assessment_id": assessment.id})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 3: Generate Roadmap ─────────────────────────────────
@agents_bp.route("/roadmap/generate", methods=["POST"])
@login_required
def generate_roadmap():
    data = request.get_json() or {}
    # Get skill gaps from latest assessment
    latest = (
        SkillAssessment.query
        .filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc())
        .first()
    )
    skill_gaps = []
    if latest and latest.skill_gaps:
        try:
            skill_gaps = json.loads(latest.skill_gaps)[:5]
        except Exception:
            pass

    domain   = data.get("domain", current_user.preferred_domain or "Technology")
    level    = data.get("level", latest.level if latest else "Beginner")
    duration = int(data.get("duration_weeks", 12))

    try:
        agent        = PersonalizedRoadmapAgent()
        roadmap_data = agent.generate_roadmap(
            domain       = domain,
            level        = level,
            career_goal  = current_user.career_goal or "Software Engineer",
            weekly_hours = current_user.weekly_hours or 10,
            duration_weeks = duration,
            skill_gaps   = skill_gaps,
        )

        # Deactivate old roadmaps
        LearningRoadmap.query.filter_by(
            student_id=current_user.id, is_active=True
        ).update({"is_active": False})

        # Save new roadmap
        roadmap = LearningRoadmap(
            student_id     = current_user.id,
            domain         = domain,
            level          = level,
            duration_weeks = duration,
            roadmap_json   = json.dumps(roadmap_data),
            is_active      = True,
        )
        db.session.add(roadmap)
        db.session.commit()

        return jsonify({
            "success":    True,
            "roadmap":    roadmap_data,
            "roadmap_id": roadmap.id,
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 4: Mentor Chat ──────────────────────────────────────
@agents_bp.route("/mentor/chat", methods=["POST"])
@login_required
def mentor_chat():
    data    = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "error": "Empty message"}), 400

    # Load recent conversation history
    recent = (
        ChatMessage.query
        .filter_by(student_id=current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(recent)]

    # Get latest assessment for context
    latest = (
        SkillAssessment.query
        .filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc())
        .first()
    )

    try:
        agent   = LearningMentorAgent()
        profile = {
            "name":             current_user.name,
            "preferred_domain": current_user.preferred_domain,
            "level":            latest.level if latest else "Beginner",
            "career_goal":      current_user.career_goal,
        }
        response = agent.chat(message, history, profile)

        # Save both messages
        db.session.add(ChatMessage(student_id=current_user.id, role="user",
                                   content=message, agent_type="mentor"))
        db.session.add(ChatMessage(student_id=current_user.id, role="assistant",
                                   content=response, agent_type="mentor"))
        db.session.commit()

        return jsonify({"success": True, "response": response})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 4: Daily Plan ───────────────────────────────────────
@agents_bp.route("/mentor/daily-plan", methods=["POST"])
@login_required
def get_daily_plan():
    latest = (
        SkillAssessment.query.filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc()).first()
    )
    active_roadmap = (
        LearningRoadmap.query.filter_by(student_id=current_user.id, is_active=True).first()
    )
    roadmap_week = None
    if active_roadmap:
        try:
            rd   = json.loads(active_roadmap.roadmap_json)
            weeks = rd.get("weeks", [])
            if weeks:
                roadmap_week = weeks[0]  # Current week (simplified)
        except Exception:
            pass

    try:
        agent   = LearningMentorAgent()
        profile = {
            "name":             current_user.name,
            "preferred_domain": current_user.preferred_domain,
            "level":            latest.level if latest else "Beginner",
            "career_goal":      current_user.career_goal,
            "weekly_hours":     current_user.weekly_hours or 10,
        }
        plan = agent.generate_daily_plan(profile, roadmap_week)
        return jsonify({"success": True, "plan": plan})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 5: Resources ────────────────────────────────────────
@agents_bp.route("/resources/recommend", methods=["POST"])
@login_required
def recommend_resources():
    data  = request.get_json() or {}
    domain = data.get("domain", current_user.preferred_domain or "Technology")
    level  = data.get("level", "Beginner")
    topic  = data.get("topic", domain)
    try:
        agent     = ResourceRecommendationAgent()
        resources = agent.recommend_resources(domain, level, topic)
        return jsonify({"success": True, "resources": resources})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 6: Career Guidance ──────────────────────────────────
@agents_bp.route("/career/plan", methods=["POST"])
@login_required
def generate_career_plan():
    latest = (
        SkillAssessment.query.filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc()).first()
    )
    try:
        agent   = CareerGuidanceAgent()
        profile = {
            "name":             current_user.name,
            "preferred_domain": current_user.preferred_domain,
            "career_goal":      current_user.career_goal,
            "level":            latest.level if latest else "Beginner",
            "current_skills":   current_user.current_skills,
            "semester":         current_user.semester,
        }
        plan = agent.generate_career_plan(profile)

        # Persist
        career = CareerGoal(
            student_id   = current_user.id,
            target_role  = current_user.career_goal,
            target_domain = current_user.preferred_domain,
            ai_guidance  = json.dumps(plan),
            required_skills_json = json.dumps(plan.get("required_skills", {})),
            certifications_json  = json.dumps(plan.get("certifications", [])),
            internship_roadmap   = json.dumps(plan.get("internship_roadmap", {})),
            resume_tips          = json.dumps(plan.get("resume_tips", [])),
            placement_prep       = json.dumps(plan.get("placement_prep", {})),
        )
        db.session.add(career)
        db.session.commit()

        return jsonify({"success": True, "plan": plan, "career_id": career.id})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 8: Projects ─────────────────────────────────────────
@agents_bp.route("/projects/recommend", methods=["POST"])
@login_required
def recommend_projects():
    latest = (
        SkillAssessment.query.filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc()).first()
    )
    skills = []
    if current_user.current_skills:
        skills = [s.strip() for s in current_user.current_skills.split(",")]

    try:
        agent = ProjectRecommendationAgent()
        projects = agent.recommend_projects(
            domain      = current_user.preferred_domain or "Technology",
            level       = latest.level if latest else "Beginner",
            career_goal = current_user.career_goal or "Software Engineer",
            skills      = skills,
            count       = 6,
        )

        # Save to DB
        saved = []
        for p in projects:
            proj = RecommendedProject(
                student_id       = current_user.id,
                title            = p.get("title", "Project"),
                description      = p.get("description", ""),
                difficulty       = p.get("difficulty", "Beginner"),
                domain           = p.get("domain", current_user.preferred_domain),
                tech_stack       = ", ".join(p.get("tech_stack", [])),
                github_template  = p.get("github_template", ""),
                estimated_hours  = p.get("estimated_hours", 20),
                learning_outcomes = json.dumps(p.get("learning_outcomes", [])),
                steps_json       = json.dumps(p.get("steps", [])),
            )
            db.session.add(proj)
            saved.append(p)
        db.session.commit()

        return jsonify({"success": True, "projects": saved})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Agent 7: Progress Analysis ────────────────────────────────
@agents_bp.route("/progress/analyse", methods=["POST"])
@login_required
def analyse_progress():
    from models import Progress
    records = (
        Progress.query.filter_by(student_id=current_user.id)
        .order_by(Progress.logged_at.desc()).limit(12).all()
    )
    active_roadmap = (
        LearningRoadmap.query.filter_by(student_id=current_user.id, is_active=True).first()
    )
    try:
        agent = ProgressTrackingAgent()
        progress_dicts = [
            {
                "week_number":      r.week_number,
                "completion_pct":   r.completion_pct,
                "total_hours_spent":r.total_hours_spent,
                "skills_gained":    r.skills_gained,
                "logged_at":        r.logged_at,
            }
            for r in records
        ]
        metrics  = agent.calculate_metrics(
            progress_dicts,
            {"duration_weeks": active_roadmap.duration_weeks} if active_roadmap else {},
        )
        analysis = agent.analyse_progress({
            "student_name": current_user.name,
            "domain":       current_user.preferred_domain,
            **metrics,
        })
        return jsonify({"success": True, "metrics": metrics, "analysis": analysis})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Concept Explainer ─────────────────────────────────────────
@agents_bp.route("/mentor/explain", methods=["POST"])
@login_required
def explain_concept():
    data    = request.get_json() or {}
    concept = data.get("concept", "")
    latest  = (
        SkillAssessment.query.filter_by(student_id=current_user.id)
        .order_by(SkillAssessment.created_at.desc()).first()
    )
    level = latest.level if latest else "Beginner"
    try:
        agent = LearningMentorAgent()
        explanation = agent.explain_concept(concept, level)
        return jsonify({"success": True, "explanation": explanation})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
