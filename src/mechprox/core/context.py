import logging
from dataclasses import dataclass, field
from typing import Any

from mechprox.core.service_registry import ServiceRegistry


@dataclass
class AppContext:
    """Shared, application-scoped context supplied to every installed module."""

    config: dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("mechprox"))
    services: ServiceRegistry = field(default_factory=ServiceRegistry)


def configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return logging.getLogger("mechprox")
