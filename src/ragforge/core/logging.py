import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter


class DailyDatedFileHandler(TimedRotatingFileHandler):
    """Writes active logs to '<prefix>-YYYY-MM-DD.log' and rolls over daily."""

    def __init__(
        self,
        log_dir: Path,
        prefix: str,
        backup_days: int = 14,
        encoding: str = "utf-8",
        utc: bool = False,
    ) -> None:
        self.log_dir = log_dir
        self.prefix = prefix
        initial_path = self._dated_path()
        super().__init__(
            filename=initial_path,
            when="midnight",
            interval=1,
            backupCount=backup_days,
            encoding=encoding,
            utc=utc,
        )
        self.suffix = "%Y-%m-%d"

    def _dated_path(self) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{self.prefix}-{date_str}.log"

    def doRollover(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore[assignment]

        new_path = self._dated_path()
        self.baseFilename = str(new_path)

        if self.backupCount > 0:
            for path in self._get_stale_files():
                path.unlink(missing_ok=True)

        if not self.delay:
            self.stream = self._open()

        new_rollover_at = self.computeRollover(int(datetime.now().timestamp()))
        while new_rollover_at <= int(datetime.now().timestamp()):
            new_rollover_at += self.interval
        self.rolloverAt = new_rollover_at

    def _get_stale_files(self) -> list[Path]:
        pattern = f"{self.prefix}-*.log"
        files = sorted(self.log_dir.glob(pattern))
        if len(files) <= self.backupCount:
            return []
        return files[: len(files) - self.backupCount]


def configure_logging(
    level: str = "INFO",
    *,
    log_to_file: bool = False,
    log_dir: Path = Path("/app/logs"),
    log_file_prefix: str = "ragforge",
    log_backup_days: int = 14,
) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
        defaults={"request_id": None},
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = DailyDatedFileHandler(
            log_dir=log_dir,
            prefix=log_file_prefix,
            backup_days=log_backup_days,
            encoding="utf-8",
            utc=False,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
