# LearnMate AI 🤖📚
### IBM SkillsBuild AICTE 2026 — Problem Statement 12
**Agentic AI for Personalized Course Pathways**

---

## 🌟 Project Overview

**LearnMate AI** is a production-ready Agentic AI web application that helps engineering students discover personalised learning paths powered by **IBM watsonx.ai Granite** models. The system deploys **8 specialised AI agents** that collaborate to deliver adaptive, personalised learning experiences.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LearnMate AI Platform                      │
├──────────────────────────────┬──────────────────────────────┤
│     Frontend (HTML+JS)       │    Flask Backend (Python)     │
│  Bootstrap 5 + Chart.js      │  8 AI Agents + watsonx.ai    │
│  Glassmorphism + Dark Mode   │  SQLite Database              │
└──────────────────────────────┴──────────────────────────────┘
                        │
          IBM watsonx.ai Granite Models
          (ibm/granite-3-8b-instruct)
```

---

## 🤖 8 AI Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **StudentProfileAgent** | Collects and analyses student profile, learning style, goals |
| 2 | **SkillAssessmentAgent** | Evaluates knowledge, classifies level (Beginner/Intermediate/Advanced), finds gaps |
| 3 | **PersonalizedRoadmapAgent** | Generates adaptive weekly/monthly learning roadmaps |
| 4 | **LearningMentorAgent** | Answers doubts, explains concepts, creates daily study plans |
| 5 | **ResourceRecommendationAgent** | Curates IBM SkillsBuild, Coursera, YouTube, GitHub resources |
| 6 | **CareerGuidanceAgent** | Career paths, certifications, internship roadmap, resume tips |
| 7 | **ProgressTrackingAgent** | Tracks streaks, completion %, hours, skill improvement |
| 8 | **ProjectRecommendationAgent** | Suggests beginner→advanced projects aligned with career goals |

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **AI / LLM** | IBM watsonx.ai — Granite 3 8B Instruct |
| **Backend** | Python 3.11, Flask 3.0 |
| **Database** | SQLite (dev) via SQLAlchemy |
| **Frontend** | HTML5, Bootstrap 5.3, Chart.js 4 |
| **Auth** | Flask-Login |
| **Migrations** | Flask-Migrate |
| **Config** | python-dotenv |

---

## 📁 Project Structure

```
learnmate_ai/
├── app.py                          # Flask app factory
├── requirements.txt
├── .env.example                    # Copy to .env
├── config/
│   ├── __init__.py
│   └── agent_instructions.py       # ✏️ CUSTOMISE AI HERE
├── agents/
│   ├── profile_agent.py            # Agent 1
│   ├── assessment_agent.py         # Agent 2
│   ├── roadmap_agent.py            # Agent 3
│   ├── mentor_agent.py             # Agent 4
│   ├── resource_agent.py           # Agent 5
│   ├── career_agent.py             # Agent 6
│   ├── progress_agent.py           # Agent 7
│   └── project_agent.py            # Agent 8
├── models/
│   └── __init__.py                 # All SQLAlchemy models
├── routes/
│   ├── auth.py                     # Login / Register / Logout
│   ├── dashboard.py                # All student pages
│   ├── agents_api.py               # JSON API for AI agents
│   └── admin.py                    # Admin panel
├── utils/
│   ├── watsonx_client.py           # IBM watsonx.ai wrapper
│   └── template_filters.py        # Jinja2 filters
├── templates/
│   ├── base.html                   # Master layout
│   ├── landing.html                # Landing page
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── index.html              # Student Dashboard
│   │   ├── chat.html               # AI Mentor Chat
│   │   ├── assessment.html         # Skill Assessment
│   │   ├── roadmap.html            # Learning Roadmap
│   │   ├── resources.html          # Resources
│   │   ├── career.html             # Career Guidance
│   │   ├── projects.html           # Projects
│   │   ├── progress.html           # Progress Tracker
│   │   ├── profile.html            # Profile
│   │   ├── profile_setup.html      # Onboarding
│   │   └── settings.html           # Settings
│   └── admin/
│       ├── dashboard.html          # Admin Dashboard
│       ├── students.html           # Student Management
│       ├── student_detail.html
│       ├── resources.html          # Resource Management
│       └── add_resource.html
└── static/
    ├── css/
    │   ├── main.css                # Global styles
    │   └── landing.css             # Landing page styles
    └── js/
        └── main.js                 # Global JavaScript
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- IBM Cloud account (free tier)
- IBM watsonx.ai project

### 1. Clone & Install
```bash
git clone <repo-url>
cd learnmate_ai
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your IBM credentials:
```env
WATSONX_API_KEY=your_ibm_watsonx_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
SECRET_KEY=your-secure-random-secret-key
```

### 3. Run the App
```bash
python app.py
```

Open `http://localhost:5000`

### 4. Admin Access
Default admin credentials (change in `.env`):
- Email: `admin@learnmate.ai`
- Password: `Admin@123456`

---

## 🔑 IBM watsonx.ai Setup

1. Create a free [IBM Cloud account](https://cloud.ibm.com)
2. Create a **watsonx.ai** project
3. Generate an **API key** at `cloud.ibm.com/iam/apikeys`
4. Copy your **Project ID** from watsonx.ai dashboard
5. Add both to your `.env` file

**Supported Models:**
- `ibm/granite-3-8b-instruct` (primary — best quality)
- `ibm/granite-3-2b-instruct` (mini — faster)

---

## ⚙️ Customising AI Behaviour

All AI agent behaviours are controlled via `config/agent_instructions.py`.

Edit the `AGENT_INSTRUCTIONS` dictionary to customise:

```python
AGENT_INSTRUCTIONS = {
    "personality": {
        "name": "LearnMate",
        "tone": "friendly, encouraging, and professional",
        "communication_style": "conversational",  # formal | conversational | motivational
    },
    "teaching_style": {
        "primary_method": "blended",              # socratic | direct | project-based | blended
        "use_analogies": True,
    },
    "safety": {
        "education_only": True,
        "refuse_off_topic": True,
    },
    # ... 10 configurable sections total
}
```

---

## 📊 Database Tables

| Table | Description |
|-------|-------------|
| `students` | User accounts + profiles |
| `skill_assessments` | Assessment results + AI feedback |
| `learning_roadmaps` | Generated learning paths |
| `progress` | Weekly learning logs |
| `resources` | Curated learning resources |
| `career_goals` | Career guidance plans |
| `recommended_projects` | AI-suggested projects |
| `daily_tasks` | Daily study tasks |
| `chat_messages` | AI mentor conversation history |

---

## 🌐 API Endpoints

| Method | Endpoint | Agent |
|--------|----------|-------|
| POST | `/api/agents/profile/analyse` | Profile Agent |
| POST | `/api/agents/assessment/questions` | Assessment Agent |
| POST | `/api/agents/assessment/evaluate` | Assessment Agent |
| POST | `/api/agents/roadmap/generate` | Roadmap Agent |
| POST | `/api/agents/mentor/chat` | Mentor Agent |
| POST | `/api/agents/mentor/daily-plan` | Mentor Agent |
| POST | `/api/agents/mentor/explain` | Mentor Agent |
| POST | `/api/agents/resources/recommend` | Resource Agent |
| POST | `/api/agents/career/plan` | Career Agent |
| POST | `/api/agents/progress/analyse` | Progress Agent |
| POST | `/api/agents/projects/recommend` | Project Agent |

---

## 🚢 Deployment

### Gunicorn (Production)
```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

### IBM Cloud Foundry
```bash
ibmcloud login
ibmcloud target --cf
ibmcloud cf push learnmate-ai -m 512M
```

Create `Procfile`:
```
web: gunicorn app:app
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

---

## 🔐 Security

- API keys stored in `.env` (never committed)
- Password hashing via Werkzeug (bcrypt)
- Flask-Login for session management
- Admin-only routes protected by decorator
- Off-topic requests refused by AI safety rules

---

## 🏆 IBM SkillsBuild AICTE 2026

This project fulfils **Problem Statement 12 — Agentic AI for Personalized Course Pathways** requirements:

- ✅ IBM watsonx.ai Granite as primary LLM
- ✅ IBM Cloud Lite services compatible
- ✅ True Agentic AI (8 specialised agents)
- ✅ Secure API key management (.env)
- ✅ Production-ready modular codebase
- ✅ 14 application pages
- ✅ Admin dashboard with export
- ✅ Glassmorphism UI + dark/light mode
- ✅ Adaptive recommendations
- ✅ IBM SkillsBuild resources prioritised

---

*LearnMate AI — Powered by IBM watsonx.ai Granite | AICTE 2026*
