import os
import logging
import logging.handlers
import sys

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(name)-24s | %(levelname)-5s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(LOGS_DIR, "solar.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        file_handler.setFormatter(_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(LOGS_DIR, "error.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        error_handler.setFormatter(_formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(_formatter)
        stream_handler.setLevel(level)
        logger.addHandler(stream_handler)

    return logger
