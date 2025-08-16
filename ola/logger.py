import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "production") == "development"


# Create log handlers
def _get_filename(base_dir="logs"):
    current_date = datetime.now().strftime("%y%m%d")
    return Path(base_dir) / f"ola-{current_date}.log"


# Create custom formatter with timezone
class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def namer(self, _):
        return _get_filename()

    def doRollover(self):
        self.stream.close()
        self.baseFilename = str(_get_filename())
        super().doRollover()


class TimeFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        return dt.strftime("%H:%M:%S,%f")[:-3]


def setup_logging() -> logging.Logger:
    # Create log handlers
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    file_handler = CustomTimedRotatingFileHandler(
        _get_filename(),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )

    formatter = TimeFormatter(
        f"[{os.getpid()}] %(asctime)s - %(levelname)s - %(message)s",
    )
    file_handler.setFormatter(formatter)

    # Get root logger and add handlers
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG if IS_DEVELOPMENT else logging.INFO)
    log.addHandler(file_handler)

    return log


# Initialize logging
logger = setup_logging()
