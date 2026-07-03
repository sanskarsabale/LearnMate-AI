"""
============================================================
LearnMate AI — Main Flask Application
IBM SkillsBuild AICTE 2026 — Problem Statement 12
============================================================
Entry point: creates the Flask app, initialises extensions,
registers blueprints, and seeds admin account on first run.
============================================================
"""

import os
import logging
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()

from models import db, Student
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.agents_api import agents_bp
from routes.admin import admin_bp
from utils.template_filters import from_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Configuration ─────────────────────────────────────────────────────
    app.config["SECRET_KEY"]            = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///learnmate.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["APP_NAME"]              = os.getenv("APP_NAME", "LearnMate AI")
    app.config["WTF_CSRF_ENABLED"]      = True

    # ── Extensions ─────────────────────────────────────────────────────────
    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access LearnMate AI."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id: str):
        return Student.query.get(int(user_id))

    # ── Blueprints ─────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(agents_bp,    url_prefix="/api/agents")
    app.register_blueprint(admin_bp,     url_prefix="/admin")

    # ── Custom Jinja2 filters ──────────────────────────────────────────────
    app.jinja_env.filters["from_json"] = from_json

    # ── Context processors ────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "current_year": datetime.utcnow().year,
        }

    # ── Database initialisation ───────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin()
        _seed_resources()

    logger.info("✅ LearnMate AI started — http://127.0.0.1:5000")
    return app


def _seed_admin():
    """Create default admin account if it doesn't exist."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@learnmate.ai")
    if not Student.query.filter_by(email=admin_email).first():
        admin = Student(
            name     = "Admin",
            email    = admin_email,
            is_admin = True,
            branch   = "Administration",
            profile_complete = True,
        )
        admin.set_password(os.getenv("ADMIN_PASSWORD", "Admin@123456"))
        db.session.add(admin)
        db.session.commit()
        logger.info("✅ Admin account seeded: %s", admin_email)


def _seed_resources():
    """Seed initial curated resources if table is empty."""
    from models import Resource
    if Resource.query.first():
        return

    resources = [
        Resource(
            title="IBM AI Foundations",
            url="https://skillsbuild.org/college-students/digital-credentials/artificial-intelligence",
            platform="IBM SkillsBuild",
            resource_type="course",
            domain="Artificial Intelligence & Machine Learning",
            level="Beginner",
            description="Core AI concepts with IBM digital credential.",
            is_free=True,
            rating=4.8,
            tags="AI,IBM,Beginner,SkillsBuild",
        ),
        Resource(
            title="Data Science Fundamentals",
            url="https://skillsbuild.org/college-students/digital-credentials/data-science",
            platform="IBM SkillsBuild",
            resource_type="course",
            domain="Data Science & Analytics",
            level="Beginner",
            description="Data science pathway with IBM credential.",
            is_free=True,
            rating=4.7,
            tags="Data Science,IBM,SkillsBuild",
        ),
        Resource(
            title="Python for Everybody",
            url="https://www.coursera.org/specializations/python",
            platform="Coursera",
            resource_type="course",
            domain="Full Stack Web Development",
            level="Beginner",
            description="Python programming specialisation by University of Michigan.",
            is_free=False,
            rating=4.8,
            tags="Python,Programming,Beginner",
        ),
        Resource(
            title="Machine Learning Crash Course",
            url="https://developers.google.com/machine-learning/crash-course",
            platform="Documentation",
            resource_type="course",
            domain="Artificial Intelligence & Machine Learning",
            level="Beginner",
            description="Google's fast-paced ML intro with TensorFlow.",
            is_free=True,
            rating=4.6,
            tags="ML,Google,Free",
        ),
        Resource(
            title="freeCodeCamp Full Stack",
            url="https://www.freecodecamp.org/learn",
            platform="freeCodeCamp",
            resource_type="course",
            domain="Full Stack Web Development",
            level="Beginner",
            description="Free full-stack certification with hands-on projects.",
            is_free=True,
            rating=4.7,
            tags="Web Dev,Free,Certification",
        ),
        Resource(
            title="Kaggle Learn",
            url="https://www.kaggle.com/learn",
            platform="Kaggle",
            resource_type="course",
            domain="Data Science & Analytics",
            level="Beginner",
            description="Hands-on ML and data science micro-courses with notebooks.",
            is_free=True,
            rating=4.5,
            tags="Kaggle,ML,Data Science,Free",
        ),
    ]
    db.session.bulk_save_objects(resources)
    db.session.commit()
    logger.info("✅ Seeded %d sample resources.", len(resources))


# ── Entry point ────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development", host="0.0.0.0", port=5000)
