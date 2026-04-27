from pathlib import Path
from typing import Any

AI_SERVICE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_CONFIG_PATH = AI_SERVICE_DIR / "model_config.yaml"


def load_model_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load model configuration from YAML."""

    target_path = config_path or DEFAULT_MODEL_CONFIG_PATH

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - runtime dependency branch
        raise RuntimeError(
            "PyYAML is required to load AI model configuration."
        ) from exc

    with target_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise ValueError("AI model configuration must be a mapping.")

    return config

def get_provider_base_url(
    ai_service_config: dict[str, Any],
    provider_id: str,
) -> str:
    """Resolve provider base URL from model_config.yaml."""

    providers = ai_service_config.get("providers", [])
    if isinstance(providers, list):
        for provider in providers:
            if not isinstance(provider, dict):
                continue
            if provider.get("id") != provider_id:
                continue
            base_url = provider.get("base_url")
            if isinstance(base_url, str) and base_url.strip():
                return base_url

    raise ValueError(f"Provider '{provider_id}' is missing base_url in model config.")

def get_provider_timeout_seconds(
    ai_service_config: dict[str, Any],
    provider_id: str,
) -> float:
    """Resolve provider timeout seconds from model_config.yaml."""

    providers = ai_service_config.get("providers", [])
    if isinstance(providers, list):
        for provider in providers:
            if not isinstance(provider, dict):
                continue
            if provider.get("id") != provider_id:
                continue
            timeout_seconds = provider.get("timeout_seconds")
            if isinstance(timeout_seconds, (int, float)) and timeout_seconds > 0:
                return float(timeout_seconds)

    raise ValueError(
        f"Provider '{provider_id}' is missing timeout_seconds in model config."
    )
