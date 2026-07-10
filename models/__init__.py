"""
============================================================
LearnMate AI — Database Models
============================================================
SQLAlchemy models for all application tables.
============================================================
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ──────────────────────────────────────────────────────────────
# Students (Users)
# ──────────────────────────────────────────────────────────────
class Student(UserMixin, db.Model):
    """Core user / student account."""
    __tablename__ = "students"

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(120), nullable=False)
    email           = db.Column(db.String(200), unique=True, nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    is_admin        = db.Column(db.Boolean, default=False)

    # Profile fields
    branch          = db.Column(db.String(100))
    semester        = db.Column(db.Integer)
    college         = db.Column(db.String(200))
    career_goal     = db.Column(db.String(200))
    preferred_domain= db.Column(db.String(120))
    learning_style  = db.Column(db.String(50))   # visual | auditory | reading | kinesthetic
    weekly_hours    = db.Column(db.Integer, default=10)
    current_skills  = db.Column(db.Text)          # comma-separated
    bio             = db.Column(db.Text)
    avatar_url      = db.Column(db.String(300))
    theme_preference= db.Column(db.String(10), default="light")  # light | dark

    # Metadata
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    last_login      = db.Column(db.DateTime)
    is_active       = db.Column(db.Boolean, default=True)
    profile_complete= db.Column(db.Boolean, default=False)

    # Relationships
    assessments     = db.relationship("SkillAssessment", back_populates="student", lazy="dynamic")
    roadmaps        = db.relationship("LearningRoadmap", back_populates="student", lazy="dynamic")
    progress_records= db.relationship("Progress", back_populates="student", lazy="dynamic")
    career_goals_rel= db.relationship("CareerGoal", back_populates="student", lazy="dynamic")
    projects        = db.relationship("RecommendedProject", back_populates="student", lazy="dynamic")
    daily_tasks     = db.relationship("DailyTask", back_populates="student", lazy="dynamic")
    chat_history    = db.relationship("ChatMessage", back_populates="student", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Student {self.email}>"


# ──────────────────────────────────────────────────────────────
# Skill Assessments
# ──────────────────────────────────────────────────────────────
class SkillAssessment(db.Model):
    """Records each skill assessment run."""
    __tablename__ = "skill_assessments"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    domain          = db.Column(db.String(120), nullable=False)
    level           = db.Column(db.String(20))      # Beginner | Intermediate | Advanced
    score           = db.Column(db.Float)            # 0-100
    skill_gaps      = db.Column(db.Text)             # JSON list of gap areas
    strengths       = db.Column(db.Text)             # JSON list of strengths
    questions_json  = db.Column(db.Text)             # JSON: questions asked
    answers_json    = db.Column(db.Text)             # JSON: student answers
    ai_feedback     = db.Column(db.Text)             # AI narrative feedback
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="assessments")

    def __repr__(self):
        return f"<Assessment {self.domain} — {self.level}>"


# ──────────────────────────────────────────────────────────────
# Learning Roadmaps
# ──────────────────────────────────────────────────────────────
class LearningRoadmap(db.Model):
    """Generated personalised learning roadmap."""
    __tablename__ = "learning_roadmaps"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    domain          = db.Column(db.String(120))
    level           = db.Column(db.String(20))
    duration_weeks  = db.Column(db.Integer, default=12)
    roadmap_json    = db.Column(db.Text, nullable=False)  # JSON: weekly plan
    milestones_json = db.Column(db.Text)                  # JSON: milestones
    is_active       = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship("Student", back_populates="roadmaps")

    def __repr__(self):
        return f"<Roadmap {self.domain} — {self.level}>"


# ──────────────────────────────────────────────────────────────
# Progress Tracking
# ──────────────────────────────────────────────────────────────
class Progress(db.Model):
    """Tracks daily/weekly learning progress per student."""
    __tablename__ = "progress"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    roadmap_id      = db.Column(db.Integer, db.ForeignKey("learning_roadmaps.id"))
    week_number     = db.Column(db.Integer)
    completed_modules = db.Column(db.Text)       # JSON list
    completion_pct  = db.Column(db.Float, default=0.0)
    streak_days     = db.Column(db.Integer, default=0)
    total_hours_spent = db.Column(db.Float, default=0.0)
    skills_gained   = db.Column(db.Text)         # JSON list
    notes           = db.Column(db.Text)
    logged_at       = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="progress_records")

    def __repr__(self):
        return f"<Progress student={self.student_id} week={self.week_number}>"


# ──────────────────────────────────────────────────────────────
# Resources
# ──────────────────────────────────────────────────────────────
class Resource(db.Model):
    """Curated learning resources managed by admin."""
    __tablename__ = "resources"

    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(300), nullable=False)
    url             = db.Column(db.String(500))
    platform        = db.Column(db.String(80))   # IBM SkillsBuild | Coursera | etc.
    resource_type   = db.Column(db.String(50))   # course | video | article | book | tool
    domain          = db.Column(db.String(120))
    level           = db.Column(db.String(20))   # Beginner | Intermediate | Advanced
    description     = db.Column(db.Text)
    is_free         = db.Column(db.Boolean, default=True)
    rating          = db.Column(db.Float, default=0.0)
    tags            = db.Column(db.String(300))  # comma-separated
    is_active       = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Resource {self.title[:40]}>"


# ──────────────────────────────────────────────────────────────
# Career Goals
# ──────────────────────────────────────────────────────────────
class CareerGoal(db.Model):
    """Student career goal and guidance plan."""
    __tablename__ = "career_goals"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    target_role     = db.Column(db.String(150))
    target_domain   = db.Column(db.String(120))
    target_company_type = db.Column(db.String(100))  # startup | MNC | research | self-employed
    timeline_months = db.Column(db.Integer, default=12)
    required_skills_json = db.Column(db.Text)        # JSON list
    certifications_json  = db.Column(db.Text)        # JSON list
    internship_roadmap   = db.Column(db.Text)        # AI-generated text
    resume_tips          = db.Column(db.Text)        # AI-generated text
    placement_prep       = db.Column(db.Text)        # AI-generated text
    ai_guidance          = db.Column(db.Text)        # Full AI guidance response
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship("Student", back_populates="career_goals_rel")

    def __repr__(self):
        return f"<CareerGoal {self.target_role}>"


# ──────────────────────────────────────────────────────────────
# Recommended Projects
# ──────────────────────────────────────────────────────────────
class RecommendedProject(db.Model):
    """AI-suggested projects for students."""
    __tablename__ = "recommended_projects"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    title           = db.Column(db.String(300), nullable=False)
    description     = db.Column(db.Text)
    difficulty      = db.Column(db.String(20))      # Beginner | Intermediate | Advanced
    domain          = db.Column(db.String(120))
    tech_stack      = db.Column(db.String(300))     # comma-separated
    github_template = db.Column(db.String(500))
    estimated_hours = db.Column(db.Integer)
    learning_outcomes = db.Column(db.Text)
    steps_json      = db.Column(db.Text)            # JSON: step-by-step guide
    is_completed    = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="projects")

    def __repr__(self):
        return f"<Project {self.title[:40]}>"


# ──────────────────────────────────────────────────────────────
# Daily Tasks
# ──────────────────────────────────────────────────────────────
class DailyTask(db.Model):
    """Daily study tasks generated for each student."""
    __tablename__ = "daily_tasks"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    task_date       = db.Column(db.Date, default=datetime.utcnow)
    task_title      = db.Column(db.String(300))
    task_description = db.Column(db.Text)
    estimated_minutes = db.Column(db.Integer, default=60)
    resource_url    = db.Column(db.String(500))
    is_completed    = db.Column(db.Boolean, default=False)
    completed_at    = db.Column(db.DateTime)
    priority        = db.Column(db.Integer, default=1)  # 1=high, 2=medium, 3=low
    task_type       = db.Column(db.String(50))           # learn | practice | revise | project

    student = db.relationship("Student", back_populates="daily_tasks")

    def __repr__(self):
        return f"<DailyTask {self.task_title[:40]}>"


# ──────────────────────────────────────────────────────────────
# Chat Messages (Mentor Agent history)
# ──────────────────────────────────────────────────────────────
class ChatMessage(db.Model):
    """Stores AI mentor chat conversation history."""
    __tablename__ = "chat_messages"

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    role            = db.Column(db.String(10), nullable=False)  # user | assistant
    content         = db.Column(db.Text, nullable=False)
    agent_type      = db.Column(db.String(50), default="mentor")  # which agent responded
    tokens_used     = db.Column(db.Integer)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="chat_history")

    def __repr__(self):
        return f"<ChatMessage {self.role} — {self.created_at}>"
