import logging
from typing import Any


# configure application logging from local configuration
def configure_logging(config: dict[str, Any]) -> None:
    logging_config = config["logging"]
    log_level = logging_config["level"]

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
        force=True,
    )

    logging.getLogger("forecast_ops").setLevel(
        getattr(logging, log_level)
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
