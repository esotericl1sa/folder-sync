from pathlib import Path
import logging
import shutil
import os


# Build maps of files and directories
def build_maps(root: Path) -> tuple[dict[Path, Path], set[Path]]:
    files: dict[Path, Path] = {}
    directories: set[Path] = set()

    if not root.exists():
        return files, directories

    for path in root.rglob("*"):
        relative = path.relative_to(root)

        if path.is_file():
            files[relative] = path
        elif path.is_dir():
            directories.add(relative)

    return files, directories


# Check if directory is writable
def check_permissions(directory: Path) -> None:
    required = os.R_OK | os.W_OK | os.X_OK

    if not os.access(directory, required):
        raise PermissionError(f"Replica folder is not accessible: {directory}")


# Remove blocking directories or files
def remove_path(path: Path, logger: logging.Logger) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path)
            logger.info("Removed blocking directory: %s", path)
        else:
            path.unlink()
            logger.info("Removed blocking file: %s", path)
    except PermissionError as exc:
        raise PermissionError(f"Cannot remove blocking path: {path}") from exc


def ensure_parent_directories(path: Path, stop_at: Path, logger: logging.Logger) -> None:
    for ancestor in path.parents:
        if ancestor == stop_at:
            break

        if ancestor.exists() and ancestor.is_file():
            remove_path(ancestor, logger)


# Create missing directories
def create_missing_dirs(source_dirs: set[Path], replica_dirs: set[Path], replica: Path, logger: logging.Logger,) -> None:
    missing_dirs = source_dirs - replica_dirs

    for directory in sorted(missing_dirs):
        destination = replica / directory
        ensure_parent_directories(destination, replica, logger)

        if destination.exists() and destination.is_file():
            remove_path(destination, logger)

        try:
            destination.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PermissionError(f"Cannot create directory: {destination}") from exc
        logger.info("Created directory: %s", destination)


# Copy files to replica
def copy_new_files(source_files: dict[Path, Path], replica_files: dict[Path, Path], replica: Path, logger: logging.Logger) -> None:
    new_files = source_files.keys() - replica_files.keys()

    for relative_path in sorted(new_files):
        source = source_files[relative_path]
        destination = replica / relative_path
        ensure_parent_directories(destination, replica, logger)

        if destination.exists() and destination.is_dir():
            remove_path(destination, logger)

        try:
            shutil.copy2(source, destination)
        except PermissionError as exc:
            raise PermissionError(f"Cannot copy file to: {destination}") from exc
        logger.info("Copied file: %s", destination)


# Helper func to compare two files
def files_are_equal(source: Path, replica: Path) -> bool:
    if source.stat().st_size != replica.stat().st_size:
        return False

    with source.open("rb") as src, replica.open("rb") as dst:
        while True:
            src_chunk = src.read(65536)
            dst_chunk = dst.read(65536)

            if src_chunk != dst_chunk:
                return False

            if not src_chunk:
                break

    return True


# Update files in replica
def update_changed_files(source_files: dict[Path, Path], replica_files: dict[Path, Path], replica: Path, logger: logging.Logger) -> None:
    common_files = source_files.keys() & replica_files.keys()

    for relative_path in sorted(common_files):
        source = source_files[relative_path]
        dest = replica / relative_path
        ensure_parent_directories(dest, replica, logger)

        if dest.exists() and dest.is_dir():
            remove_path(dest, logger)

        if not files_are_equal(source, dest):
            try:
                shutil.copy2(source, dest)
            except PermissionError as exc:
                raise PermissionError(f"Cannot update file: {dest}") from exc
            logger.info("Updated file: %s", dest)


# Delete extra files in replica
def delete_extra_files(source_files: dict[Path, Path], replica_files: dict[Path, Path], logger: logging.Logger) -> None:
    extra_files = replica_files.keys() - source_files.keys()

    for relative_path in sorted(extra_files):
        path = replica_files[relative_path]

        try:
            path.unlink()
        except PermissionError as exc:
            raise PermissionError(f"Cannot delete file: {path}") from exc
        logger.info("Deleted file: %s", path)


# Delete extra dirs in replica
def delete_extra_directories(source_dirs: set[Path], replica_dirs: set[Path], replica: Path, logger: logging.Logger) -> None:
    extra_dirs = replica_dirs - source_dirs

    # Delete deepest dirs first
    for relative_path in sorted(extra_dirs, key=lambda path: len(path.parts), reverse=True):
        directory = replica / relative_path

        try:
            directory.rmdir()
        except PermissionError as exc:
            raise PermissionError(f"Cannot delete directory: {directory}") from exc
        logger.info("Deleted directory: %s", directory)


# Perform sync between source and replica
def sync(source: Path, replica: Path, logger: logging.Logger) -> None:
    logger.info("Sync in process...")

    try:
        replica.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(f"Cannot create replica folder: {replica}") from exc

    check_permissions(replica)

    source_files, source_dirs = build_maps(source)
    replica_files, replica_dirs = build_maps(replica)

    create_missing_dirs(source_dirs, replica_dirs, replica, logger)

    copy_new_files(source_files, replica_files, replica, logger)

    update_changed_files(source_files, replica_files, replica, logger)

    delete_extra_files(source_files, replica_files, logger)

    delete_extra_directories(source_dirs, replica_dirs, replica, logger)
