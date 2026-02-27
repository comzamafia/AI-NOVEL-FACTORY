"""
LLM Provider abstraction layer.

Supports multiple backends:
  - OllamaProvider  : Local models via Ollama (default for dev/testing)
  - GeminiProvider  : Google Gemini API (production)

Switch via settings.LLM_PROVIDER = 'ollama' | 'gemini'
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# Base interface
# ─────────────────────────────────────────────────────────

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> dict:
        """
        Send a chat request.

        Args:
            messages: List of {"role": "...", "content": "..."} dicts
            max_tokens: Max output tokens
            temperature: 0.0–1.0 creativity
            json_mode: If True, force JSON output (provider support varies)

        Returns:
            {
                "content": str,       # generated text
                "model": str,         # model name used
                "tokens_in": int,
                "tokens_out": int,
                "cost_usd": float,
            }
        """

    def generate(self, prompt: str, **kwargs) -> dict:
        """Convenience: single-turn prompt → response."""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )


# ─────────────────────────────────────────────────────────
# Ollama Provider
# ─────────────────────────────────────────────────────────

class OllamaProvider(BaseLLMProvider):
    """
    Local LLM via Ollama.

    Ollama exposes an OpenAI-compatible endpoint at:
        http://localhost:11434/v1/chat/completions

    Start Ollama and pull a model before use:
        ollama serve
        ollama pull llama3
    """

    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3')
        self.timeout = getattr(settings, 'OLLAMA_TIMEOUT', 300)  # 5 min for long chapters
        self._endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> dict:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        logger.debug(f"[Ollama] POST {self._endpoint} model={self.model} tokens={max_tokens}")

        try:
            resp = requests.post(
                self._endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure 'ollama serve' is running."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout}s. "
                "Try a smaller model or increase OLLAMA_TIMEOUT."
            )

        data = resp.json()

        # OpenAI-compatible response format
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})

        return {
            "content": content,
            "model": data.get("model", self.model),
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "cost_usd": 0.0,  # Local model = free
        }

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is pulled."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            if resp.status_code != 200:
                return False
            models = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
            model_name = self.model.split(":")[0]
            return model_name in models
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Return list of locally available Ollama models."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []


# ─────────────────────────────────────────────────────────
# Gemini Provider (future)
# ─────────────────────────────────────────────────────────

class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider.
    Activate by setting LLM_PROVIDER='gemini' in settings / .env
    Requires: pip install google-generativeai
    """

    # Pricing per 1M tokens (gemini-2.0-flash as of 2025)
    COST_PER_M_IN = 0.075
    COST_PER_M_OUT = 0.30

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in settings/environment.")

    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 8192,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> dict:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Run: pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        model = genai.GenerativeModel(self.model, generation_config=config)

        # Convert OpenAI-style messages to Gemini format
        history = []
        system_prompt = ""
        user_prompt = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_prompt = content
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})

        full_prompt = f"{system_prompt}\n\n{user_prompt}".strip() if system_prompt else user_prompt

        response = model.generate_content(full_prompt)
        text = response.text

        # Estimate tokens (Gemini doesn't always return exact counts)
        tokens_in = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        tokens_out = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        cost = (tokens_in / 1_000_000 * self.COST_PER_M_IN) + \
               (tokens_out / 1_000_000 * self.COST_PER_M_OUT)

        return {
            "content": text,
            "model": self.model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 6),
        }


# ─────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────

def get_llm_provider() -> BaseLLMProvider:
    """
    Return the active LLM provider based on settings.LLM_PROVIDER.

    Settings:
        LLM_PROVIDER = 'ollama'   (default)
        LLM_PROVIDER = 'gemini'
    """
    provider_name = getattr(settings, 'LLM_PROVIDER', 'ollama').lower()

    if provider_name == 'ollama':
        return OllamaProvider()
    elif provider_name == 'gemini':
        return GeminiProvider()
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            "Valid options: 'ollama', 'gemini'"
        )
