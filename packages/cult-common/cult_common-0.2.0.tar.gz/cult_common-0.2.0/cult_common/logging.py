import logging
from logging.config import dictConfig
from pythonjsonlogger.json import JsonFormatter

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(event_id)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}


def setup_logging() -> None:
    dictConfig(DEFAULT_LOGGING)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)

