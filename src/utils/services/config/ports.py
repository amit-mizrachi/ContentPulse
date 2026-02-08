"""Service port configuration utilities."""
import os

from src.utils.services.aws.appconfig_service import get_config_service


def get_service_port(
    appconfig_key: str,
    env_var: str = "SERVICE_PORT",
    default: int = 8000
) -> int:
    """Get service port. Priority: env var > AppConfig > default."""
    env_port = os.environ.get(env_var)
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass

    try:
        appconfig = get_config_service()
        port = appconfig.get(appconfig_key)
        if port is not None:
            return int(port)
    except Exception:
        pass

    return default
