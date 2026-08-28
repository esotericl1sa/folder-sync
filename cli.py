from pathlib import Path
import sys


# Read command line args
def read_args() -> tuple[Path, Path, int, int, Path]:
    # Script name and 5 args
    if len(sys.argv) != 6:
        raise ValueError("Expected args: <source> <replica> <sync_interval> <sync_count> <log_file>")

    source = Path(sys.argv[1])
    replica = Path(sys.argv[2])
    log_file = Path(sys.argv[5])

    try:
        sync_interval = int(sys.argv[3])
        sync_count = int(sys.argv[4])
    except ValueError as e:
        raise ValueError(f"Sync interval and sync count must be integers: {e}")

    return source, replica, sync_interval, sync_count, log_file