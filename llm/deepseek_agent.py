from __future__ import annotations
from typing import Dict


class DeepSeekAgent:
    """
    Stub for DeepSeek Chat LLM integration via OpenRouter.
    For offline mode, returns simple messages.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def plan_task(self, prompt: str) -> str:
        """
        Given a prompt describing tasks and context, returns a simple response.
        In a real implementation this would call the LLM with guardrails.
        """
        # Return a generic response since offline mode cannot call LLMs
        return "This feature is coming soon."