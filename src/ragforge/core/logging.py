import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def configure_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()

    root_logger.setLevel(level.upper())

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(
        JsonFormatter(
            fmt=("%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"),
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
            defaults={"request_id": None},
        )
    )

    root_logger.addHandler(handler)
