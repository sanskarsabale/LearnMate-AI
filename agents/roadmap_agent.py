"""
============================================================
Agent 3 — Personalized Roadmap Agent
============================================================
Generates weekly / monthly learning roadmaps.
Adapts when student level or progress changes.
============================================================
"""

import json
import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class PersonalizedRoadmapAgent:
    """Creates adaptive personalised learning roadmaps."""

    SYSTEM_PROMPT = """You are an expert curriculum designer for LearnMate AI.
Generate structured, actionable, and realistic learning roadmaps.
Always return valid JSON when asked for structured output.
Roadmaps must be tailored to the student's level, goals, and time availability."""

    def generate_roadmap(
        self,
        domain: str,
        level: str,
        career_goal: str,
        weekly_hours: int,
        duration_weeks: int = 12,
        skill_gaps: list | None = None,
    ) -> dict:
        """
        Generate a full weekly roadmap.

        Returns:
            {weeks: [...], milestones: [...], summary: str}
        """
        gaps_text = ", ".join(skill_gaps) if skill_gaps else "general fundamentals"

        prompt = f"""
Create a detailed {duration_weeks}-week personalised learning roadmap for a student.

Profile:
- Domain: {domain}
- Current Level: {level}
- Career Goal: {career_goal}
- Weekly Study Time: {weekly_hours} hours
- Key Skill Gaps: {gaps_text}

Return ONLY a valid JSON object with this structure:
{{
  "title": "Roadmap title",
  "duration_weeks": {duration_weeks},
  "summary": "2-sentence overview of the roadmap",
  "weeks": [
    {{
      "week": 1,
      "theme": "Week theme/focus",
      "topics": ["Topic 1", "Topic 2", "Topic 3"],
      "tasks": ["Task 1", "Task 2"],
      "project": "Mini project or exercise",
      "hours_required": {weekly_hours},
      "milestone": "What the student can do after this week"
    }}
  ],
  "milestones": [
    {{"week": 4, "title": "Month 1 Milestone", "description": "..."}}
  ]
}}

Do NOT include any text before or after the JSON.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["roadmap_agent"]
        raw = watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **cfg,
        )

        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(raw[start:end])
                return data
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Roadmap parsing failed: %s", exc)

        return self._fallback_roadmap(domain, level, duration_weeks, weekly_hours)

    def adapt_roadmap(
        self,
        current_roadmap: dict,
        completed_weeks: int,
        current_performance: str,
        new_level: str | None = None,
    ) -> dict:
        """
        Adapt existing roadmap based on progress.

        Args:
            current_roadmap:      Previously generated roadmap dict.
            completed_weeks:      How many weeks completed.
            current_performance:  'ahead' | 'on-track' | 'behind'
            new_level:            Updated level if assessment changed it.

        Returns:
            Updated roadmap dict.
        """
        prompt = f"""
A student's learning roadmap needs adaptation.

Current Status:
- Completed: {completed_weeks} weeks
- Performance: {current_performance}
- New assessed level: {new_level or 'unchanged'}
- Remaining roadmap JSON: {json.dumps(current_roadmap.get('weeks', [])[completed_weeks:completed_weeks+4])}

Adjust the next 4 weeks of the roadmap accordingly:
- If 'ahead': increase difficulty and add advanced topics.
- If 'behind': slow down, add revision, reduce topics per week.
- If 'on-track': maintain pace, add slight variety.

Return ONLY the updated JSON array for the adjusted weeks in the same format.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["roadmap_agent"]
        raw = watsonx.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, **cfg)

        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                adapted_weeks = json.loads(raw[start:end])
                all_weeks = current_roadmap.get("weeks", [])
                all_weeks[completed_weeks:completed_weeks + len(adapted_weeks)] = adapted_weeks
                current_roadmap["weeks"] = all_weeks
                current_roadmap["adapted"] = True
                return current_roadmap
        except Exception as exc:
            logger.warning("Roadmap adaptation failed: %s", exc)

        return current_roadmap  # Return original if adaptation fails

    # ------------------------------------------------------------------
    # Fallback roadmap (no AI)
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_roadmap(
        domain: str, level: str, duration_weeks: int, weekly_hours: int
    ) -> dict:
        weeks = []
        themes = [
            "Foundations & Setup",
            "Core Concepts",
            "Intermediate Techniques",
            "Practical Applications",
            "Projects & Integration",
            "Advanced Topics",
            "Review & Assessment",
            "Specialisation",
            "Industry Practices",
            "Capstone Project",
            "Portfolio Building",
            "Career Preparation",
        ]
        for i in range(min(duration_weeks, 12)):
            weeks.append({
                "week": i + 1,
                "theme": themes[i % len(themes)],
                "topics": [f"Topic {i*3+1}", f"Topic {i*3+2}", f"Topic {i*3+3}"],
                "tasks": [f"Practice exercise {i+1}", f"Mini quiz week {i+1}"],
                "project": f"Week {i+1} project",
                "hours_required": weekly_hours,
                "milestone": f"Complete week {i+1} objectives",
            })
        return {
            "title": f"{domain} — {level} Roadmap",
            "duration_weeks": duration_weeks,
            "summary": f"A structured {duration_weeks}-week path for {domain} at {level} level.",
            "weeks": weeks,
            "milestones": [
                {"week": 4,  "title": "Month 1 Complete", "description": "Core foundations covered"},
                {"week": 8,  "title": "Month 2 Complete", "description": "Intermediate skills acquired"},
                {"week": 12, "title": "Month 3 Complete", "description": "Ready for projects"},
            ],
        }
