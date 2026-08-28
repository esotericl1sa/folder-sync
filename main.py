import time

from cli import read_args
from sync_logging import init_logger
from fs_sync import sync


def main():
    source, replica, sync_interval, sync_count, log_file = read_args()

    # Handle invalid args
    if not source.exists():
        raise ValueError(f"Source path doesn't exist: {source}")
    if not source.is_dir():
        raise ValueError(f"Source path isn't a directory: {source}")
    if replica.exists() and not replica.is_dir():
        raise ValueError(f"Replica path exists but isn't a directory: {replica}")
    if sync_count < 1:
        raise ValueError(f"Sync count must be >= 1, got {sync_count}")
    if sync_interval < 0:
        raise ValueError(f"Sync interval must be >= 0, got {sync_interval}")

    logger = init_logger(log_file)

    for i in range(sync_count):
        logger.info("Starting sync %d/%d", i + 1, sync_count)

        sync(source, replica, logger)

        if i < sync_count - 1:
            time.sleep(sync_interval)
    logger.info("Sync finished!")


if __name__ == "__main__":
    main()
