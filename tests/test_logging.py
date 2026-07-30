import logging

from saltbytes.logging import configure_logging


def test_configure_logging_sets_application_level() -> None:
    config = {
        "logging": {
            "level": "DEBUG",
        }
    }

    configure_logging(config)

    assert (
        logging.getLogger("saltbytes").getEffectiveLevel()
        == logging.DEBUG
    )
    assert logging.getLogger("httpx").getEffectiveLevel() == logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() == logging.WARNING