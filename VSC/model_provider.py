import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None


DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _get_config_value(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value:
        return value

    if st is None:
        return default

    try:
        secret_value = st.secrets.get(name)
    except Exception:
        secret_value = None

    if secret_value:
        os.environ[name] = str(secret_value)
        return str(secret_value)

    return default


def get_api_key() -> str | None:
    return _get_config_value("OPENAI_API_KEY")


def has_api_key() -> bool:
    return bool(get_api_key())


def get_missing_api_key_message() -> str:
    return "OPENAI_API_KEY is missing. Add it to Streamlit secrets or your environment variables before rebuilding the index or asking questions."


def get_chat_model_name() -> str:
    return _get_config_value("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL) or DEFAULT_CHAT_MODEL


def get_embedding_model_name() -> str:
    return _get_config_value("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL) or DEFAULT_EMBEDDING_MODEL


def build_embeddings() -> OpenAIEmbeddings:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(get_missing_api_key_message())
    return OpenAIEmbeddings(model=get_embedding_model_name(), api_key=api_key)


def build_llm() -> ChatOpenAI:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(get_missing_api_key_message())
    return ChatOpenAI(model=get_chat_model_name(), api_key=api_key, temperature=0)