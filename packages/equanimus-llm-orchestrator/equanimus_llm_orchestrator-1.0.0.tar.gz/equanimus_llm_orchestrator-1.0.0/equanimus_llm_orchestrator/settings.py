from django.conf import settings


def validate_settings_variables():
    required_vars = [
        "LLM_MAX_INPUT_TOKENS",
        "LLM_MAX_CONTEXT_TOKENS",
        "DB_URL",
        "LLM_TYPE",
        "LLM_MODEL_NAME",
        "LLM_EMBEDDING_MODEL_NAME",
        "AWS_ACCESS_KEY_ID",
        "AWS_DEFAULT_REGION",
        "AWS_SECRET_ACCESS_KEY",
        "CHROMA_HOST",
        "CHROMA_PORT",
        "CHROMA_USER",
        "CHROMA_PASSWORD",
        "CHROMA_AUTH_PROVIDER",
    ]

    missing_vars = [var for var in required_vars if not hasattr(settings, var)]

    if missing_vars:
        raise ValueError(f"As seguintes variáveis não estão definidas em settings: {', '.join(missing_vars)}")
