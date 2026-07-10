"""
============================================================
Agent 1 — Student Profile Agent
============================================================
Collects and analyses student profile data.
Generates a personalised onboarding summary.
============================================================
"""

import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class StudentProfileAgent:
    """Analyses student profile and produces a learning-readiness summary."""

    SYSTEM_PROMPT = """You are LearnMate, a warm and welcoming AI learning mentor.
Your role is to greet new students, understand their background, and create a
personalised welcome summary. Be encouraging, professional, and concise.
Only discuss educational topics. Always respond in English."""

    def analyse_profile(self, profile: dict) -> str:
        """
        Generate a personalised profile summary.

        Args:
            profile: dict with keys: name, branch, semester, career_goal,
                     preferred_domain, learning_style, weekly_hours, current_skills

        Returns:
            AI-generated profile analysis string.
        """
        cfg = AGENT_INSTRUCTIONS
        tone = cfg["response_tone"]["student_profile_agent"]

        prompt = f"""
A new student has completed their profile. Analyse their background and create
a personalised welcome message with a brief learning readiness summary.

Student Profile:
- Name: {profile.get('name', 'Student')}
- Branch: {profile.get('branch', 'Not specified')}
- Semester: {profile.get('semester', 'Not specified')}
- Career Goal: {profile.get('career_goal', 'Not specified')}
- Preferred Domain: {profile.get('preferred_domain', 'Not specified')}
- Learning Style: {profile.get('learning_style', 'Not specified')}
- Weekly Study Hours: {profile.get('weekly_hours', 10)}
- Current Skills: {profile.get('current_skills', 'None listed')}
- Bio: {profile.get('bio', '')}

Instructions:
1. Greet the student warmly by name.
2. Acknowledge their goals and domain interest.
3. Comment on their learning style and weekly availability.
4. Mention 2-3 skill gaps they should focus on first.
5. Encourage them to take the Skill Assessment next.
6. Keep response under 250 words. Tone: {tone}.
"""
        params = cfg["model_params"]["default"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **params,
        )

    def suggest_learning_style_tips(self, learning_style: str) -> str:
        """Return tips based on the student's declared learning style."""
        prompt = f"""
The student's preferred learning style is: {learning_style}

Provide 5 practical, concise tips on how they can maximise their learning
using this style. Format as a numbered list. Keep each tip under 30 words.
"""
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_new_tokens=400,
            temperature=0.6,
        )
