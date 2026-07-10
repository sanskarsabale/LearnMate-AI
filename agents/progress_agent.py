"""
============================================================
Agent 7 — Progress Tracking Agent
============================================================
Tracks completed modules, learning streak, weekly progress,
skill improvement, and overall completion percentage.
Generates progress summaries and improvement suggestions.
============================================================
"""

import logging
from datetime import datetime, timedelta
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class ProgressTrackingAgent:
    """Analyses and reports on student learning progress."""

    SYSTEM_PROMPT = """You are a progress analytics expert for LearnMate AI.
Analyse student learning data and provide constructive, data-driven insights.
Celebrate achievements, identify blockers, and suggest improvements.
Be analytical but encouraging in tone."""

    def analyse_progress(self, progress_data: dict) -> str:
        """
        Generate an AI analysis of current progress.

        Args:
            progress_data: {
                student_name, domain, total_weeks, completed_weeks,
                completion_pct, streak_days, total_hours, skills_gained,
                weekly_scores
            }

        Returns:
            AI-generated progress report string.
        """
        name        = progress_data.get("student_name", "Student")
        domain      = progress_data.get("domain", "your domain")
        total_weeks = progress_data.get("total_weeks", 12)
        comp_weeks  = progress_data.get("completed_weeks", 0)
        comp_pct    = progress_data.get("completion_pct", 0)
        streak      = progress_data.get("streak_days", 0)
        hours       = progress_data.get("total_hours", 0)
        skills      = progress_data.get("skills_gained", [])
        tone        = AGENT_INSTRUCTIONS["response_tone"]["progress_agent"]

        skills_text = ", ".join(skills) if skills else "None recorded yet"

        prompt = f"""
Analyse this student's learning progress and write an encouraging, insightful report.

Student: {name}
Domain: {domain}
Progress: {comp_weeks}/{total_weeks} weeks completed ({comp_pct:.1f}%)
Learning Streak: {streak} days
Total Study Hours: {hours:.1f} hours
Skills Gained: {skills_text}

Write a progress report (150-200 words) that:
1. Celebrates specific achievements (streak, hours, skills).
2. Identifies whether they're ahead, on-track, or behind.
3. Highlights the top 2 improvement areas.
4. Suggests 3 concrete actions for this week.
5. Ends with a motivating closing line.

Tone: {tone}
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["default"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **cfg,
        )

    def calculate_metrics(self, progress_records: list, roadmap: dict | None = None) -> dict:
        """
        Calculate all progress metrics from database records.

        Args:
            progress_records: List of Progress model dicts.
            roadmap:          Active roadmap dict.

        Returns:
            Computed metrics dict.
        """
        if not progress_records:
            return {
                "completion_pct":  0,
                "streak_days":     0,
                "total_hours":     0,
                "completed_weeks": 0,
                "total_weeks":     roadmap.get("duration_weeks", 12) if roadmap else 12,
                "skills_gained":   [],
                "weekly_progress": [],
                "avg_daily_hours": 0,
            }

        total_hours      = sum(r.get("total_hours_spent", 0) for r in progress_records)
        completed_weeks  = len(progress_records)
        total_weeks      = roadmap.get("duration_weeks", 12) if roadmap else 12
        completion_pct   = round((completed_weeks / total_weeks) * 100, 1)

        # Skills gained
        skills_gained = []
        for r in progress_records:
            sg = r.get("skills_gained", "")
            if sg:
                import json
                try:
                    skills_gained.extend(json.loads(sg))
                except Exception:
                    skills_gained.extend([s.strip() for s in sg.split(",") if s.strip()])

        # Calculate streak
        streak = self._calculate_streak(progress_records)

        # Weekly progress chart data
        weekly_progress = [
            {
                "week":  r.get("week_number", i + 1),
                "pct":   r.get("completion_pct", 0),
                "hours": r.get("total_hours_spent", 0),
            }
            for i, r in enumerate(progress_records)
        ]

        avg_daily_hours = round(total_hours / max(len(progress_records) * 7, 1), 1)

        return {
            "completion_pct":  completion_pct,
            "streak_days":     streak,
            "total_hours":     round(total_hours, 1),
            "completed_weeks": completed_weeks,
            "total_weeks":     total_weeks,
            "skills_gained":   list(set(skills_gained)),
            "weekly_progress": weekly_progress,
            "avg_daily_hours": avg_daily_hours,
        }

    @staticmethod
    def _calculate_streak(progress_records: list) -> int:
        """Calculate current consecutive-days streak."""
        if not progress_records:
            return 0
        dates = sorted(
            set(r.get("logged_at", datetime.utcnow()).date() if hasattr(r.get("logged_at", None), "date")
                else datetime.utcnow().date()
                for r in progress_records),
            reverse=True,
        )
        if not dates:
            return 0

        streak = 1
        for i in range(1, len(dates)):
            if (dates[i - 1] - dates[i]).days == 1:
                streak += 1
            else:
                break
        return streak

    def get_improvement_suggestions(self, metrics: dict, domain: str) -> str:
        """AI suggestions based on progress metrics."""
        comp   = metrics.get("completion_pct", 0)
        streak = metrics.get("streak_days", 0)
        hours  = metrics.get("total_hours", 0)

        prompt = f"""
A student learning {domain} has these metrics:
- Completion: {comp}%
- Streak: {streak} days
- Total hours: {hours}

Give 3 specific, actionable improvement suggestions based on their data.
Keep each suggestion under 40 words. Format as a numbered list.
"""
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_new_tokens=300,
            temperature=0.6,
        )
