# Folder Sync

Python command-line utility that synchronizes a source directory with
a replica directory. The replica is made to match the source: new and changed
files are copied, missing directories are created, and files or directories
that exist only in the replica are removed.

## Features

- Recursive synchronization, including nested directories
- Byte-for-byte comparison before updating existing files
- File metadata preservation through `shutil.copy2`
- Choose a sync interval and number of sync cycles
- Console and file logging
- Automatic creation of the replica and log-file parent directories

The project uses only the Python standard library.

## Project Structure

```text
folder-sync/
├── main.py         # Entry point and validation
├── cli.py          # Command-line argument parsing
├── fs_sync.py      # Directory comparison and synchronization logic
├── sync_logging.py # Console and file logger setup
├── sync_tests.py   # Built-in integration-style tests
└── README.md
```

## Installation and usage

Clone the repository:

```bash
git clone https://github.com/esotericl1sa/folder-sync.git
```

Run the program from the project directory:

```bash
python3 main.py <source> <replica> <sync_interval> <sync_count> <log_file>
```

Arguments:

| Argument | Description |
| --- | --- |
| `source` | Existing directory to copy from |
| `replica` | Directory to keep synchronized; created if necessary |
| `sync_interval` | Seconds between sync cycles; a non-negative integer |
| `sync_count` | Number of sync cycles; an integer of at least `1` |
| `log_file` | Log-file path; parent directories are created if necessary |

Example:

```bash
python3 main.py ./source ./replica 10 3 ./logs/sync.log
```

This performs a sync immediately, waits 10 seconds, performs the second sync,
waits again, and then performs the final sync. With `sync_count` set to `1`,
the command runs once without waiting.

### Synchronization behavior

The source directory is authoritative. During each cycle, the program:

1. Creates directories present in the source but missing from the replica.
2. Copies new files and replaces changed files.
3. Removes files and empty directories that exist only in the replica.

Use a replica path that does not contain unrelated data because extra content
in the replica is deleted.

## Testing

Run the built-in tests with:

```bash
python3 sync_tests.py
```

The tests use temporary directories and do not modify the repository's
`source/`, `replica/`, or `logs/` directories.

## License

This project is available under the MIT License.