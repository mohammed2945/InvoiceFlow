import os
from typing import Optional

_statsd = None
_statsd_initialized = False


def _service_name() -> str:
    return os.environ.get("DD_SERVICE", "invoice-api")


def _env_name() -> str:
    return os.environ.get("DD_ENV", "local")


def _version_name() -> str:
    return os.environ.get("DD_VERSION", "local")


def _default_tags(extra_tags: Optional[list[str]] = None) -> list[str]:
    tags = [
        f"service:{_service_name()}",
        f"env:{_env_name()}",
        f"version:{_version_name()}",
    ]
    if extra_tags:
        tags.extend(extra_tags)
    return tags


def _get_statsd():
    global _statsd, _statsd_initialized
    if _statsd_initialized:
        return _statsd
    _statsd_initialized = True
    try:
        from datadog import DogStatsd

        host = os.environ.get("DD_AGENT_HOST", "localhost")
        port = int(os.environ.get("DD_DOGSTATSD_PORT", "8125"))
        _statsd = DogStatsd(host=host, port=port)
    except Exception:
        _statsd = None
    return _statsd


def increment(name: str, value: int = 1, extra_tags: Optional[list[str]] = None) -> None:
    client = _get_statsd()
    if client is None:
        return
    try:
        client.increment(name, value, tags=_default_tags(extra_tags))
    except Exception:
        pass


def gauge(name: str, value: float, extra_tags: Optional[list[str]] = None) -> None:
    client = _get_statsd()
    if client is None:
        return
    try:
        client.gauge(name, value, tags=_default_tags(extra_tags))
    except Exception:
        pass


def timing(name: str, value_ms: float, extra_tags: Optional[list[str]] = None) -> None:
    client = _get_statsd()
    if client is None:
        return
    try:
        client.timing(name, value_ms, tags=_default_tags(extra_tags))
    except Exception:
        pass
