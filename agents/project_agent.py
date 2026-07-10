"""
============================================================
Agent 8 — Project Recommendation Agent
============================================================
Suggests beginner, intermediate, and advanced projects
aligned with student career goals and skill level.
============================================================
"""

import json
import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class ProjectRecommendationAgent:
    """Recommends personalised projects at appropriate difficulty levels."""

    SYSTEM_PROMPT = """You are a project mentor for LearnMate AI.
Suggest innovative, portfolio-worthy projects that demonstrate real-world skills.
Projects must be achievable for students given their level and timeframe.
IBM Cloud, Watson AI, or open-source tech should be incorporated where possible.
Always return valid JSON when asked for structured output."""

    def recommend_projects(
        self,
        domain: str,
        level: str,
        career_goal: str,
        skills: list | None = None,
        count: int = 6,
    ) -> list:
        """
        Generate personalised project recommendations.

        Returns:
            List of project dicts.
        """
        skills_text = ", ".join(skills) if skills else "general " + domain + " skills"
        per_level   = max(count // 3, 1)

        prompt = f"""
Recommend {per_level} Beginner, {per_level} Intermediate, and {per_level} Advanced
projects for a student in {domain} aiming to become a {career_goal}.

Student current skills: {skills_text}

Return ONLY a valid JSON array. Each project must have:
{{
  "title": "Project title",
  "description": "2-3 sentence project description",
  "difficulty": "Beginner|Intermediate|Advanced",
  "domain": "{domain}",
  "tech_stack": ["tech1", "tech2", "tech3"],
  "estimated_hours": 20,
  "learning_outcomes": ["outcome1", "outcome2", "outcome3"],
  "github_template": "https://github.com/search?q={domain}+project",
  "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "ibm_integration": "Optional: how to use IBM Watson/Cloud here"
}}

Do NOT include text before or after the JSON array.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["default"]
        raw = watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_new_tokens=cfg.get("max_new_tokens", 1200),
            temperature=0.6,
            top_p=0.92,
        )

        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                projects = json.loads(raw[start:end])
                return projects[:count]
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Project parsing failed: %s", exc)

        return self._fallback_projects(domain, level)

    def get_project_guide(self, project_title: str, tech_stack: list, level: str) -> str:
        """Generate a step-by-step project implementation guide."""
        stack = ", ".join(tech_stack)
        prompt = f"""
Create a detailed step-by-step implementation guide for this project:
"{project_title}"

Tech stack: {stack}
Student level: {level}

Provide:
1. Project setup (environment, tools, libraries)
2. Core feature implementation (5-7 steps)
3. Testing approach
4. Deployment option (Heroku / IBM Cloud / GitHub Pages)
5. Portfolio presentation tips

Keep structured and actionable. Under 500 words.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["default"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **cfg,
        )

    @staticmethod
    def _fallback_projects(domain: str, level: str) -> list:
        return [
            {
                "title": f"{domain} Beginner Project",
                "description": f"A starter project to build foundational {domain} skills.",
                "difficulty": "Beginner",
                "domain": domain,
                "tech_stack": ["Python", "Jupyter Notebook"],
                "estimated_hours": 15,
                "learning_outcomes": ["Apply basics", "Version control with Git", "Documentation"],
                "github_template": f"https://github.com/search?q={domain.replace(' ', '+')}+beginner",
                "steps": ["Setup environment", "Build core feature", "Test and document"],
                "ibm_integration": "Use IBM Watson Text-to-Speech API",
            },
            {
                "title": f"{domain} Intermediate Project",
                "description": f"A project that applies intermediate {domain} concepts.",
                "difficulty": "Intermediate",
                "domain": domain,
                "tech_stack": ["Python", "Flask", "SQLite"],
                "estimated_hours": 30,
                "learning_outcomes": ["Full-stack integration", "API usage", "Database design"],
                "github_template": f"https://github.com/search?q={domain.replace(' ', '+')}+intermediate",
                "steps": ["Design architecture", "Implement features", "Deploy to cloud"],
                "ibm_integration": "Deploy on IBM Cloud Foundry",
            },
            {
                "title": f"{domain} Advanced Capstone",
                "description": f"An end-to-end advanced {domain} application for portfolio.",
                "difficulty": "Advanced",
                "domain": domain,
                "tech_stack": ["Python", "Docker", "IBM Cloud", "React"],
                "estimated_hours": 60,
                "learning_outcomes": ["System design", "Cloud deployment", "CI/CD pipeline"],
                "github_template": f"https://github.com/search?q={domain.replace(' ', '+')}+advanced",
                "steps": ["System design", "Full implementation", "Testing suite", "CI/CD", "Production deploy"],
                "ibm_integration": "Full IBM watsonx.ai integration",
            },
        ]
