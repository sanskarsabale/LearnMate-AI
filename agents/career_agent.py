"""
============================================================
Agent 6 — Career Guidance Agent
============================================================
Recommends career paths, required skills, certifications,
internship roadmaps, placement prep, and resume tips.
============================================================
"""

import json
import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class CareerGuidanceAgent:
    """Provides comprehensive career planning and guidance."""

    SYSTEM_PROMPT = """You are a career guidance expert for LearnMate AI.
You help students from engineering/technology backgrounds plan their
careers professionally. Focus on realistic, actionable advice.
IBM certifications and cloud skills should be highlighted when relevant.
Always return valid JSON when asked for structured output."""

    def generate_career_plan(self, student_profile: dict) -> dict:
        """
        Generate a complete career guidance plan.

        Returns:
            {
              career_paths, required_skills, certifications,
              internship_roadmap, placement_prep, resume_tips, summary
            }
        """
        domain  = student_profile.get("preferred_domain", "Artificial Intelligence & Machine Learning")
        goal    = student_profile.get("career_goal", "Software Engineer")
        level   = student_profile.get("level", "Beginner")
        skills  = student_profile.get("current_skills", "Python basics")
        semester = student_profile.get("semester", 3)
        cfg     = AGENT_INSTRUCTIONS["career_domains"]

        prompt = f"""
Create a comprehensive career guidance plan for an engineering student.

Profile:
- Target Domain: {domain}
- Career Goal: {goal}
- Current Level: {level}
- Current Skills: {skills}
- Semester: {semester}
- IBM certifications priority: {cfg['ibm_certifications_priority']}

Return ONLY a valid JSON object:
{{
  "summary": "2-sentence career overview",
  "career_paths": [
    {{"role": "...", "description": "...", "avg_salary": "...", "demand": "High|Medium|Low"}}
  ],
  "required_skills": {{
    "technical": ["skill1", "skill2"],
    "soft": ["skill1", "skill2"],
    "tools": ["tool1", "tool2"]
  }},
  "certifications": [
    {{"name": "...", "provider": "IBM|Google|AWS|...", "url": "...", "priority": 1}}
  ],
  "internship_roadmap": {{
    "semester_{semester}": "Focus on...",
    "semester_{semester+1}": "Apply for...",
    "summer": "Target companies..."
  }},
  "placement_prep": {{
    "technical_rounds": "...",
    "coding_practice": "...",
    "system_design": "...",
    "timeline": "..."
  }},
  "resume_tips": ["tip1", "tip2", "tip3", "tip4", "tip5"]
}}

Do NOT include text before or after the JSON.
"""
        career_cfg = AGENT_INSTRUCTIONS["model_params"]["career_agent"]
        raw = watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **career_cfg,
        )

        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Career plan parsing failed: %s", exc)

        return self._fallback_career_plan(domain, goal)

    def get_resume_tips(self, domain: str, level: str) -> list:
        """Return actionable resume tips for the domain."""
        prompt = f"""
List 7 specific, actionable resume tips for a {level} student targeting {domain} roles.
Format as a JSON array of strings. Each tip should be under 60 words.
Return ONLY the JSON array.
"""
        raw = watsonx.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT,
                               max_new_tokens=500, temperature=0.5)
        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return [
            "Quantify achievements with numbers wherever possible.",
            "Highlight IBM SkillsBuild and Coursera certifications.",
            "Include GitHub profile with active repositories.",
            "Use action verbs: Built, Developed, Designed, Deployed.",
            "Keep resume to 1 page for freshers.",
        ]

    def get_interview_prep(self, domain: str, role: str) -> str:
        """Generate interview preparation guide."""
        prompt = f"""
Create a 30-day interview preparation guide for a {domain} role as {role}.

Include:
1. Week-by-week breakdown
2. Key topics to cover
3. Practice platforms (LeetCode, HackerRank, etc.)
4. Mock interview resources
5. Common questions to prepare

Keep response structured and under 400 words.
"""
        career_cfg = AGENT_INSTRUCTIONS["model_params"]["career_agent"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **career_cfg,
        )

    @staticmethod
    def _fallback_career_plan(domain: str, goal: str) -> dict:
        return {
            "summary": f"Build a strong foundation in {domain} and work towards becoming a {goal}.",
            "career_paths": [
                {"role": goal, "description": f"Expert in {domain}", "avg_salary": "₹6–15 LPA", "demand": "High"},
                {"role": "Research Engineer", "description": "R&D and innovation", "avg_salary": "₹8–20 LPA", "demand": "Medium"},
            ],
            "required_skills": {
                "technical": ["Python", "Machine Learning", "Cloud Computing"],
                "soft": ["Communication", "Problem Solving", "Teamwork"],
                "tools": ["Git", "Docker", "IBM Watson"],
            },
            "certifications": [
                {"name": "IBM AI Developer", "provider": "IBM", "url": "https://skillsbuild.org", "priority": 1},
                {"name": "Google Associate Cloud Engineer", "provider": "Google", "url": "https://cloud.google.com/certification", "priority": 2},
            ],
            "internship_roadmap": {
                "current": "Build portfolio projects",
                "next_semester": "Apply to internships on LinkedIn & Internshala",
                "summer": "Target product-based companies",
            },
            "placement_prep": {
                "technical_rounds": "Data Structures, Algorithms, System Design",
                "coding_practice": "LeetCode, HackerRank, CodeChef",
                "system_design": "Learn after core DSA",
                "timeline": "Start 6 months before placements",
            },
            "resume_tips": [
                "Keep it to 1 page with clean formatting.",
                "Add GitHub link with live projects.",
                "List certifications from IBM SkillsBuild.",
                "Quantify every achievement you list.",
                "Tailor resume to each job description.",
            ],
        }
