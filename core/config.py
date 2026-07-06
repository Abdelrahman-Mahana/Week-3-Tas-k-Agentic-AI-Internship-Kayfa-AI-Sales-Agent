"""
Central configuration module for Kayfa Sales Agent.
Loads environment variables and defines provider-agnostic pricing tables.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Dict, Tuple
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)


class Settings:
    """Application settings loaded from environment variables."""

    # --- OpenAI (fallback) ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )

    # --- OpenRouter (fallback) ---
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # --- Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Gemini (primary) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

    # --- MongoDB ---
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "kayfa_sales_agent")

    # --- App ---
    DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- Paths ---
    DATA_DIR: Path = PROJECT_ROOT / "data"
    JSON_DIR: Path = DATA_DIR / "json"
    TEXT_DIR: Path = DATA_DIR / "text"
    VECTORSTORE_DIR: Path = PROJECT_ROOT / "rag" / "vectorstore"

    # -----------------------------------------------------------------------
    # Provider-aware helpers
    # -----------------------------------------------------------------------
    @property
    def llm_api_key(self) -> str:
        """Return the active LLM API key (Gemini preferred, then Groq, then OpenRouter, then OpenAI)."""
        return self.GEMINI_API_KEY or self.GROQ_API_KEY or self.OPENROUTER_API_KEY or self.OPENAI_API_KEY

    @property
    def llm_base_url(self) -> str | None:
        """Return the OpenAI-compatible base URL, or None for native OpenAI."""
        if self.GEMINI_API_KEY:
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        if self.GROQ_API_KEY:
            return "https://api.groq.com/openai/v1"
        if self.OPENROUTER_API_KEY:
            return "https://openrouter.ai/api/v1"
        return None

    @property
    def llm_provider(self) -> str:
        """Return the logical provider name for logging/cost tracking."""
        if self.GEMINI_API_KEY:
            return "google"
        if self.GROQ_API_KEY:
            return "groq"
        if self.OPENROUTER_API_KEY:
            return "openrouter"
        return "openai"

    @property
    def llm_model(self) -> str:
        """Return the chat model identifier to use."""
        if self.GEMINI_API_KEY:
            return self.GEMINI_MODEL
        if self.GROQ_API_KEY:
            return self.GROQ_MODEL
        return self.LLM_MODEL or self.OPENAI_CHAT_MODEL

    @property
    def use_gemini(self) -> bool:
        """Return True if Gemini is configured as the active provider."""
        return bool(self.GEMINI_API_KEY)

    @property
    def embedding_model(self) -> str:
        """Return the embedding model identifier to use."""
        if self.GEMINI_API_KEY:
            return self.GEMINI_EMBEDDING_MODEL
        return self.OPENAI_EMBEDDING_MODEL

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing critical configuration."""
        missing = []
        if (
            not cls.GEMINI_API_KEY
            and not cls.GROQ_API_KEY
            and not cls.OPENROUTER_API_KEY
            and (not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == "sk-your-openai-api-key-here")
        ):
            missing.append("GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, or OPENAI_API_KEY")
        if not cls.MONGODB_URI:
            missing.append("MONGODB_URI")
        return missing


# ---------------------------------------------------------------------------
# Provider-agnostic pricing table (USD per 1K tokens)
# ---------------------------------------------------------------------------
# Structure: { (provider, model): { "input": float, "output": float, "embedding": float } }
# "embedding" is per 1K tokens for embedding models.
# ---------------------------------------------------------------------------

PRICING_TABLE: Dict[Tuple[str, str], Dict[str, float]] = {
    # OpenAI chat models
    ("openai", "gpt-4o"): {"input": 0.00500, "output": 0.01500},
    ("openai", "gpt-4o-mini"): {"input": 0.00015, "output": 0.00060},
    ("openai", "gpt-4-turbo"): {"input": 0.01000, "output": 0.03000},
    ("openai", "gpt-3.5-turbo"): {"input": 0.00050, "output": 0.00150},
    # OpenAI embedding models
    ("openai", "text-embedding-3-small"): {"embedding": 0.00002},
    ("openai", "text-embedding-3-large"): {"embedding": 0.00013},
    ("openai", "text-embedding-ada-002"): {"embedding": 0.00010},
    # OpenRouter chat models
    ("openrouter", "openai/gpt-oss-120b:free"): {"input": 0.0, "output": 0.0},
    ("openrouter", "openai/gpt-4o-mini"): {"input": 0.00015, "output": 0.00060},
    ("openrouter", "openai/gpt-4o"): {"input": 0.00500, "output": 0.01500},
    ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"): {"input": 0.0, "output": 0.0},
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"): {"input": 0.0, "output": 0.0},
    ("openrouter", "google/gemma-4-31b-it:free"): {"input": 0.0, "output": 0.0},
    # OpenRouter embedding models
    ("openrouter", "openai/text-embedding-3-small"): {"embedding": 0.00002},
    ("openrouter", "openai/text-embedding-3-large"): {"embedding": 0.00013},
    # Google Gemini models
    ("google", "gemini-2.0-flash"): {"input": 0.000075, "output": 0.00030},
    ("google", "gemini-1.5-flash"): {"input": 0.000075, "output": 0.00030},
    ("google", "gemini-1.5-pro"): {"input": 0.00125, "output": 0.00500},
    ("google", "text-embedding-004"): {"embedding": 0.00000},
    ("google", "embedding-001"): {"embedding": 0.00000},
    # Groq models
    ("groq", "llama-3.3-70b-versatile"): {"input": 0.00059, "output": 0.00079},
    ("groq", "llama-3.1-70b-versatile"): {"input": 0.00059, "output": 0.00079},
    ("groq", "llama-3.1-8b-instant"): {"input": 0.00005, "output": 0.00008},
    ("groq", "mixtral-8x7b-32768"): {"input": 0.00024, "output": 0.00024},
    ("groq", "gemma2-9b-it"): {"input": 0.00020, "output": 0.00020},
    # Placeholder entries for future providers (cost-monitor must handle gracefully)
    ("anthropic", "claude-3-5-sonnet-20241022"): {"input": 0.00300, "output": 0.01500},
    ("anthropic", "claude-3-haiku-20240307"): {"input": 0.00025, "output": 0.00125},
    ("google", "gemini-1.5-flash"): {"input": 0.000075, "output": 0.00030},
    ("google", "gemini-1.5-pro"): {"input": 0.00125, "output": 0.00500},
}


def get_pricing(provider: str, model: str) -> Dict[str, float] | None:
    """Lookup pricing for a given (provider, model) tuple.

    Returns None if no pricing entry exists — callers should handle gracefully.
    """
    key = (provider.lower(), model.lower())
    return PRICING_TABLE.get(key)


def estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """Estimate cost in USD for a given LLM call.

    Returns 0.0 if pricing is not found (provider-agnostic fallback).
    """
    try:
        from genai_prices import Usage, calc_price
        price_info = calc_price(
            Usage(input_tokens=input_tokens, output_tokens=output_tokens),
            model_ref=model,
            provider_id=provider
        )
        if price_info is not None:
            return float(price_info.total_price)
    except Exception:
        # Fall back to local pricing table if genai-prices is not installed
        # or if calculation fails
        pass

    pricing = get_pricing(provider, model)
    if pricing is None:
        return 0.0

    cost = 0.0
    if "input" in pricing and input_tokens:
        cost += (input_tokens / 1000) * pricing["input"]
    if "output" in pricing and output_tokens:
        cost += (output_tokens / 1000) * pricing["output"]
    return round(cost, 8)


def estimate_embedding_cost(provider: str, model: str, total_tokens: int) -> float:
    """Estimate cost in USD for embedding tokens.

    Returns 0.0 if pricing is not found.
    """
    try:
        from genai_prices import Usage, calc_price
        price_info = calc_price(
            Usage(input_tokens=total_tokens, output_tokens=0),
            model_ref=model,
            provider_id=provider
        )
        if price_info is not None:
            return float(price_info.total_price)
    except Exception:
        # Fall back to local pricing table
        pass

    pricing = get_pricing(provider, model)
    if pricing is None or "embedding" not in pricing:
        return 0.0
    return round((total_tokens / 1000) * pricing["embedding"], 8)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()

