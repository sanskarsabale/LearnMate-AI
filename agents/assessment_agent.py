"""
============================================================
Agent 2 — Skill Assessment Agent
============================================================
Evaluates current student knowledge.
Classifies level: Beginner / Intermediate / Advanced.
Identifies skill gaps and strengths.
============================================================
"""

import json
import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class SkillAssessmentAgent:
    """Conducts AI-driven skill assessments and scores students."""

    SYSTEM_PROMPT = """You are an expert technical assessor for LearnMate AI.
Your job is to evaluate student knowledge objectively and constructively.
Always return valid JSON when asked for structured output.
Be encouraging even when pointing out gaps."""

    def generate_questions(self, domain: str, level: str = "auto", count: int = 10) -> list:
        """
        Generate assessment questions for a domain.

        Returns:
            List of question dicts: {question, options: [A,B,C,D], correct, explanation}
        """
        prompt = f"""
Generate {count} multiple-choice assessment questions to evaluate a student's
knowledge in: {domain}

Difficulty level: {level} (use "auto" to mix easy, medium, hard)

Return ONLY a valid JSON array. Each item must have:
{{
  "question": "...",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "correct": "A",
  "explanation": "Brief explanation of the correct answer",
  "difficulty": "easy|medium|hard"
}}

Do NOT include any text before or after the JSON array.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["assessment_agent"]
        raw = watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **cfg,
        )

        # Parse JSON safely
        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Question parsing failed: %s", exc)

        # Fallback demo questions
        return self._fallback_questions(domain)

    def evaluate_answers(
        self,
        domain: str,
        questions: list,
        answers: dict,
    ) -> dict:
        """
        Score answers and return assessment result.

        Args:
            domain:    Subject domain.
            questions: List of question dicts.
            answers:   {question_index: selected_option} e.g. {"0": "A", "1": "C"}

        Returns:
            {score, level, skill_gaps, strengths, feedback, percentage}
        """
        correct = 0
        total   = len(questions)
        gaps    = []
        strengths = []

        for i, q in enumerate(questions):
            student_ans = answers.get(str(i), "")
            if student_ans == q.get("correct", ""):
                correct += 1
                strengths.append(q.get("question", "")[:60])
            else:
                gaps.append({
                    "question": q.get("question", "")[:80],
                    "topic": domain,
                    "explanation": q.get("explanation", ""),
                })

        percentage = round((correct / total) * 100, 1) if total > 0 else 0
        cfg        = AGENT_INSTRUCTIONS["difficulty"]

        if percentage >= cfg["auto_upgrade_threshold"]:
            level = "Advanced"
        elif percentage >= 50:
            level = "Intermediate"
        else:
            level = "Beginner"

        # Generate AI feedback
        feedback = self._generate_feedback(domain, percentage, level, gaps[:3])

        return {
            "score":       correct,
            "total":       total,
            "percentage":  percentage,
            "level":       level,
            "skill_gaps":  gaps,
            "strengths":   strengths,
            "feedback":    feedback,
        }

    def _generate_feedback(
        self, domain: str, percentage: float, level: str, top_gaps: list
    ) -> str:
        gaps_text = "\n".join(
            f"- {g['question'][:60]}" for g in top_gaps
        ) or "None identified"

        prompt = f"""
A student just completed a skill assessment in {domain}.
Score: {percentage}% → Level: {level}

Top skill gaps identified:
{gaps_text}

Write a constructive 3-4 sentence feedback message:
1. Acknowledge their performance.
2. Name the specific gaps they should address first.
3. Encourage them and suggest the next step (start their personalised roadmap).
Keep it under 120 words. Tone: objective and constructive but encouraging.
"""
        cfg = AGENT_INSTRUCTIONS["model_params"]["assessment_agent"]
        return watsonx.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT, **cfg)

    # ------------------------------------------------------------------
    # Fallback when AI is unavailable
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_questions(domain: str) -> list:
        return [
            {
                "question": f"What is a fundamental concept in {domain}?",
                "options": {
                    "A": "Abstraction",
                    "B": "Colour theory",
                    "C": "Cooking techniques",
                    "D": "Sports statistics",
                },
                "correct": "A",
                "explanation": "Abstraction is a core principle in most technical domains.",
                "difficulty": "easy",
            }
        ]
