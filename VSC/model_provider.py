import json
import os
from urllib.error import URLError
from urllib.request import urlopen

from langchain_ollama import OllamaEmbeddings, OllamaLLM


DEFAULT_CHAT_MODEL = "mistral:latest"
DEFAULT_EMBEDDING_MODEL = "mistral:latest"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


def _get_config_value(name: str, default: str) -> str:
    return os.environ.get(name, default)


def get_ollama_host() -> str:
    return _get_config_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")


def get_chat_model_name() -> str:
    return _get_config_value("OLLAMA_CHAT_MODEL", DEFAULT_CHAT_MODEL)


def get_embedding_model_name() -> str:
    return _get_config_value("OLLAMA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def get_missing_api_key_message() -> str:
    return (
        "Ollama is not reachable. Start the Ollama app or run `ollama serve`, then make sure "
        f"the models `{get_chat_model_name()}` and `{get_embedding_model_name()}` are available."
    )


def has_api_key() -> bool:
    return ollama_is_available()


def ollama_is_available() -> bool:
    try:
        with urlopen(f"{get_ollama_host()}/api/tags", timeout=2) as response:
            return response.status == 200
    except (URLError, TimeoutError):
        return False


def get_ollama_status_message() -> str | None:
    if not ollama_is_available():
        return get_missing_api_key_message()

    try:
        with urlopen(f"{get_ollama_host()}/api/tags", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (json.JSONDecodeError, URLError, TimeoutError):
        return "Ollama responded unexpectedly. Restart it and retry."

    model_names = {model.get("name") for model in payload.get("models", [])}
    missing_models = [
        model_name
        for model_name in (get_chat_model_name(), get_embedding_model_name())
        if model_name not in model_names
    ]
    if missing_models:
        missing_text = ", ".join(missing_models)
        return f"Missing Ollama models: {missing_text}. Run `ollama pull` for each missing model before rebuilding the index."

    return None


def build_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=get_embedding_model_name(), base_url=get_ollama_host())


def build_llm() -> OllamaLLM:
    return OllamaLLM(model=get_chat_model_name(), base_url=get_ollama_host())