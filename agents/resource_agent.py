"""
============================================================
Agent 5 — Resource Recommendation Agent
============================================================
Curates and recommends learning resources from:
IBM SkillsBuild, Docs, GitHub, YouTube, Coursera,
freeCodeCamp, and Kaggle — personalised by level & domain.
============================================================
"""

import json
import logging
from config.agent_instructions import AGENT_INSTRUCTIONS
from utils.watsonx_client import watsonx

logger = logging.getLogger(__name__)


class ResourceRecommendationAgent:
    """AI-curated resource recommendations per topic and level."""

    SYSTEM_PROMPT = """You are a learning resource curator for LearnMate AI.
Recommend high-quality, actionable learning resources from trusted platforms.
IBM SkillsBuild should always be included when relevant.
Always return valid JSON when asked for structured output."""

    # Curated fallback resources used when AI is unavailable
    CURATED_RESOURCES = {
        "Artificial Intelligence & Machine Learning": [
            {
                "title": "IBM AI Fundamentals",
                "platform": "IBM SkillsBuild",
                "url": "https://skillsbuild.org/college-students/digital-credentials/artificial-intelligence",
                "type": "course",
                "level": "Beginner",
                "free": True,
            },
            {
                "title": "Machine Learning Specialization",
                "platform": "Coursera",
                "url": "https://www.coursera.org/specializations/machine-learning-introduction",
                "type": "course",
                "level": "Intermediate",
                "free": False,
            },
            {
                "title": "Kaggle ML Courses",
                "platform": "Kaggle",
                "url": "https://www.kaggle.com/learn",
                "type": "course",
                "level": "Beginner",
                "free": True,
            },
        ],
        "Data Science & Analytics": [
            {
                "title": "IBM Data Science Professional Certificate",
                "platform": "IBM SkillsBuild",
                "url": "https://skillsbuild.org/college-students/digital-credentials/data-science",
                "type": "course",
                "level": "Beginner",
                "free": True,
            },
        ],
        "Full Stack Web Development": [
            {
                "title": "Responsive Web Design",
                "platform": "freeCodeCamp",
                "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
                "type": "course",
                "level": "Beginner",
                "free": True,
            },
            {
                "title": "The Odin Project",
                "platform": "GitHub",
                "url": "https://github.com/TheOdinProject",
                "type": "course",
                "level": "Intermediate",
                "free": True,
            },
        ],
    }

    def recommend_resources(
        self,
        domain: str,
        level: str,
        topic: str,
        max_results: int = 5,
    ) -> list:
        """
        Recommend curated resources for a specific topic.

        Returns:
            List of resource dicts with title, platform, url, type, level, free.
        """
        cfg = AGENT_INSTRUCTIONS["platforms"]

        prompt = f"""
Recommend {max_results} specific learning resources for:
- Domain: {domain}
- Level: {level}
- Topic: {topic}

Prioritise: IBM SkillsBuild (always include if available), then
{', '.join(cfg['primary'])}, then {', '.join(cfg['secondary'])}.
Free resources first: {cfg['free_resources_first']}.

Return ONLY a valid JSON array. Each item must have:
{{
  "title": "Resource title",
  "platform": "Platform name",
  "url": "https://actual-url.com",
  "type": "course|video|article|documentation|repository",
  "level": "{level}",
  "free": true,
  "description": "1-2 sentences on what students will learn",
  "estimated_hours": 5
}}

Do NOT include text before or after the JSON array.
"""
        resource_cfg = AGENT_INSTRUCTIONS["model_params"]["resource_agent"]
        raw = watsonx.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            **resource_cfg,
        )

        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                resources = json.loads(raw[start:end])
                return resources[:max_results]
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Resource parsing failed: %s", exc)

        # Fallback to curated resources
        return self.CURATED_RESOURCES.get(domain, self.CURATED_RESOURCES[
            "Artificial Intelligence & Machine Learning"
        ])[:max_results]

    def recommend_for_roadmap_week(self, domain: str, level: str, week_topics: list) -> list:
        """Get resources for all topics in a roadmap week."""
        all_resources = []
        for topic in week_topics[:3]:  # Limit to 3 topics per week
            resources = self.recommend_resources(domain, level, topic, max_results=2)
            all_resources.extend(resources)
        return all_resources

    def get_ibm_skillsbuild_courses(self, domain: str) -> list:
        """Return IBM SkillsBuild–specific course recommendations."""
        prompt = f"""
List 5 specific IBM SkillsBuild courses or learning paths for: {domain}

Return ONLY a JSON array:
[{{"title": "...", "url": "https://skillsbuild.org/...", "duration": "X hours", "level": "...", "credential": true}}]
"""
        raw = watsonx.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT,
                               max_new_tokens=400, temperature=0.4)
        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return [
            {
                "title": f"IBM SkillsBuild — {domain}",
                "url":  "https://skillsbuild.org/college-students",
                "duration": "Self-paced",
                "level": "All levels",
                "credential": True,
            }
        ]
