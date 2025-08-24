import os


def load_r2_config() -> dict[str, str]:
    """Load required R2 storage configuration from environment variables."""
    required = [
        "R2_ENDPOINT_URL",
        "R2_BUCKET_NAME",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"Missing R2 configuration variables: {', '.join(missing)}"
        )
    return {
        "endpoint_url": os.environ["R2_ENDPOINT_URL"],
        "bucket": os.environ["R2_BUCKET_NAME"],
        "access_key": os.environ["R2_ACCESS_KEY_ID"],
        "secret_key": os.environ["R2_SECRET_ACCESS_KEY"],
    }
