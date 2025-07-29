import sys
from .core import heimdall_ping_point

def register_ping(app=None, framework=None, route="/__ping__"):
    if framework is None:
        # Auto-detect
        if "flask" in sys.modules:
            framework = "flask"
        elif "fastapi" in sys.modules:
            framework = "fastapi"
        elif "django" in sys.modules:
            framework = "django"
        else:
            raise ImportError(
                "No supported web framework detected (Flask, FastAPI, Django)"
            )

    if framework == "flask":
        from .flask_impl import register_ping as flask_ping
        return flask_ping(app, route)
    elif framework == "fastapi":
        from .fastapi_impl import register_ping as fastapi_ping
        return fastapi_ping(app, route)
    elif framework == "django":
        from .django_impl import register_ping as django_ping
        return django_ping()
    else:
        raise ValueError(f"Unsupported framework: {framework}")

__all__ = ["register_ping", "heimdall_ping_point"]
