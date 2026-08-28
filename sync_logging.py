from pathlib import Path
import logging


def close_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)

# Configure logging
def init_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("folder_sync")

    if logger.handlers:
        close_logger(logger)

    logger.setLevel(logging.INFO)

    # Create a log file if it doesn't exist
    if log_path.is_dir():
        log_path = log_path / "log.txt"

    log_path.parent.mkdir(parents=True, exist_ok=True)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
