"""
============================================================
LearnMate AI — IBM watsonx.ai Granite Client
============================================================
Thin wrapper around ibm-watsonx-ai SDK.
All agents use this module to call Granite models.
============================================================
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy import: only fails at call time if package missing
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False
    logger.warning("ibm-watsonx-ai not installed — running in MOCK mode.")


class WatsonXClient:
    """
    Singleton client for IBM watsonx.ai Granite models.

    Usage:
        client = WatsonXClient()
        response = client.generate(prompt="Explain Python decorators")
    """

    _instance: Optional["WatsonXClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._client = None
        self._model_cache: dict = {}
        self._api_key    = os.getenv("WATSONX_API_KEY", "")
        self._project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self._url        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self._default_model_id = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct")
        self._mini_model_id    = os.getenv("GRANITE_MINI_MODEL_ID", "ibm/granite-3-2b-instruct")

        if WATSONX_AVAILABLE and self._api_key and self._project_id:
            try:
                credentials = Credentials(
                    url=self._url,
                    api_key=self._api_key,
                )
                self._client = APIClient(credentials=credentials, project_id=self._project_id)
                logger.info("✅ WatsonX client initialised successfully.")
            except Exception as exc:
                logger.error("❌ WatsonX init failed: %s", exc)
                self._client = None
        else:
            logger.warning("⚠️  WatsonX credentials missing or SDK unavailable — MOCK mode active.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_model(self, model_id: str, params: dict) -> "ModelInference":
        """Return a cached ModelInference for the given model_id + params combo."""
        key = f"{model_id}:{hash(str(params))}"
        if key not in self._model_cache:
            self._model_cache[key] = ModelInference(
                model_id=model_id,
                api_client=self._client,
                params=params,
                project_id=self._project_id,
            )
        return self._model_cache[key]

    def _mock_response(self, prompt: str) -> str:
        """Fallback mock used when WatsonX is unavailable."""
        return (
            "🤖 **[Demo Mode]** IBM watsonx.ai is not configured yet.\n\n"
            "To enable full AI responses:\n"
            "1. Copy `.env.example` → `.env`\n"
            "2. Add your `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`\n"
            "3. Restart the server\n\n"
            f"*(Your prompt received: {prompt[:80]}...)*"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_new_tokens: int = 800,
        temperature: float = 0.7,
        top_p: float = 0.95,
        repetition_penalty: float = 1.1,
        use_mini: bool = False,
    ) -> str:
        """
        Generate text using IBM Granite.

        Args:
            prompt:            User / task prompt.
            system_prompt:     System instruction (persona, rules).
            max_new_tokens:    Max tokens to generate.
            temperature:       Sampling temperature.
            top_p:             Nucleus sampling probability.
            repetition_penalty Penalise repeated tokens.
            use_mini:          Use smaller/faster Granite model.

        Returns:
            Generated text string.
        """
        if not self._client:
            return self._mock_response(prompt)

        model_id = self._mini_model_id if use_mini else self._default_model_id

        params = {
            GenParams.MAX_NEW_TOKENS:      max_new_tokens,
            GenParams.TEMPERATURE:         temperature,
            GenParams.TOP_P:               top_p,
            GenParams.REPETITION_PENALTY:  repetition_penalty,
        }

        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

        try:
            model = self._get_model(model_id, params)
            result = model.generate_text(prompt=full_prompt)
            return result.strip()
        except Exception as exc:
            logger.error("WatsonX generation error: %s", exc)
            return f"⚠️ AI temporarily unavailable. Error: {str(exc)[:200]}"

    def is_available(self) -> bool:
        """Return True if watsonx.ai client is configured and ready."""
        return self._client is not None


# Module-level singleton
watsonx = WatsonXClient()
