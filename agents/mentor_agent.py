"""
============================================================
Agent 4 — Learning Mentor Agent
============================================================
Answers doubts, explains concepts, suggests next steps,
generates daily study plans, and motivates students.
This is the primary conversational agent.
============================================================
"""

import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class LearningMentorAgent:
    """Conversational AI mentor — the student's personal tutor."""

    def _build_system_prompt(self, student_profile: dict | None = None) -> str:
        cfg = AGENT_INSTRUCTIONS
        p   = cfg["personality"]
        t   = cfg["teaching_style"]
        s   = cfg["safety"]
        ep  = cfg["educational_policies"]

        profile_context = ""
        if student_profile:
            profile_context = f"""
Student Context:
- Name: {student_profile.get('name', 'Student')}
- Domain: {student_profile.get('preferred_domain', 'General')}
- Level: {student_profile.get('level', 'Beginner')}
- Career Goal: {student_profile.get('career_goal', 'Not specified')}
"""

        return f"""You are {p['name']}, an AI {p['role']} for LearnMate AI — an IBM SkillsBuild initiative.

Your personality: {p['tone']}, {p['communication_style']} communication style.
Teaching approach: {t['primary_method']} method. Use analogies: {t['use_analogies']}.
Use real-world examples: {t['use_real_world_examples']}.
Guide students without giving direct answers to homework: {ep['guide_dont_solve']}.
Always cite sources when mentioning platforms: {ep['cite_sources']}.
Educational only: {s['education_only']}.
Off-topic redirect: "{s['off_topic_redirect_message']}"
{profile_context}
Respond concisely. Format code in markdown code blocks."""

    def chat(
        self,
        user_message: str,
        conversation_history: list | None = None,
        student_profile: dict | None = None,
    ) -> str:
        """
        Respond to a student's message in chat.

        Args:
            user_message:          Latest student message.
            conversation_history:  List of {role, content} dicts (recent N messages).
            student_profile:       Student context dict.

        Returns:
            AI response string.
        """
        system_prompt = self._build_system_prompt(student_profile)

        # Build conversation context
        history_text = ""
        if conversation_history:
            # Use last 10 messages to stay within token budget
            for msg in conversation_history[-10:]:
                role    = "Student" if msg["role"] == "user" else "LearnMate"
                history_text += f"{role}: {msg['content']}\n"

        prompt = f"""Previous conversation:
{history_text}

Student: {user_message}

LearnMate:"""

        cfg = AGENT_INSTRUCTIONS["model_params"]["mentor_agent"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            **cfg,
        )

    def generate_daily_plan(self, student_profile: dict, roadmap_week: dict | None = None) -> str:
        """Generate a personalised daily study plan for today."""
        domain   = student_profile.get("preferred_domain", "Technology")
        level    = student_profile.get("level", "Beginner")
        hours    = student_profile.get("weekly_hours", 10)
        daily_hrs = round(hours / 5, 1)
        topics   = roadmap_week.get("topics", []) if roadmap_week else []
        topic_text = ", ".join(topics) if topics else "core fundamentals"

        prompt = f"""
Generate a detailed, motivating daily study plan for today.

Student:
- Domain: {domain}
- Level: {level}
- Available today: {daily_hrs} hours
- Current week's topics: {topic_text}

Create a time-blocked daily plan with:
1. Warm-up activity (15 min)
2. Core learning session (topic, resource type)
3. Practice exercise
4. Break schedule
5. Evening revision (30 min)
6. Daily motivation tip

Make it realistic and encouraging. Total time ≤ {daily_hrs} hours.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["mentor_agent"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self._build_system_prompt(student_profile),
            **cfg,
        )

    def explain_concept(self, concept: str, level: str = "Beginner") -> str:
        """Explain a specific concept at the appropriate level."""
        prompt = f"""
Explain the concept: "{concept}" for a {level}-level student.

Structure your explanation as:
1. Simple one-line definition
2. Real-world analogy
3. Core details (3-4 bullet points)
4. Code example (if applicable, in Python or pseudocode)
5. Common mistakes to avoid
6. What to learn next

Keep the total response under 400 words.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["mentor_agent"]
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self._build_system_prompt(),
            **cfg,
        )

    def get_motivation(self, context: str = "") -> str:
        """Return a personalised motivational message."""
        cfg  = AGENT_INSTRUCTIONS["motivation"]
        style = cfg["style"]
        phrases = cfg["motivational_phrases"]

        prompt = f"""
Generate a short, genuine motivational message for a student who is learning technology.
Motivation style: {style}.
Context: {context or 'general encouragement'}

Keep it under 60 words. Be authentic, not clichéd.
You can incorporate one of these if appropriate: {phrases[0]}
"""
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self._build_system_prompt(),
            max_new_tokens=150,
            temperature=0.8,
        )

    def suggest_next_step(self, student_profile: dict, completed_topic: str) -> str:
        """Suggest the next learning step after completing a topic."""
        domain = student_profile.get("preferred_domain", "Technology")
        level  = student_profile.get("level", "Beginner")

        prompt = f"""
A {level} student in {domain} just completed: "{completed_topic}"

Suggest the ideal NEXT learning step:
1. Name the next topic (be specific)
2. Why it's the natural progression (1 sentence)
3. Best resource to start with (platform + type)
4. Estimated time to complete

Keep response under 100 words. Be direct and actionable.
"""
        return watsonx.generate(
            prompt=prompt,
            system_prompt=self._build_system_prompt(student_profile),
            max_new_tokens=200,
            temperature=0.5,
        )
