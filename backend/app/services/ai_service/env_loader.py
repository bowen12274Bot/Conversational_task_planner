import os
from pathlib import Path

AI_SERVICE_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
PROVIDER_API_KEYS = {
    "ai_studio": "AI_STUDIO_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def load_env_value(key: str) -> str | None:
    """Load an environment value from process env first, then backend/.env."""

    value = os.getenv(key)
    if value:
        return value

    if not AI_SERVICE_ENV_PATH.exists():
        return None

    with AI_SERVICE_ENV_PATH.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            env_key, env_value = line.split("=", 1)
            if env_key.strip() == key:
                cleaned = env_value.strip().strip('"').strip("'")
                return cleaned or None

    return None


def load_provider_api_key(provider_id: str) -> str | None:
    """Load API key for a supported provider."""

    env_key = PROVIDER_API_KEYS.get(provider_id)
    if not env_key:
        return None

    return load_env_value(env_key)
