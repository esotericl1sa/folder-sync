import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


SCRIPT = Path(__file__).parent / "main.py"


@contextmanager
def sync_env():
    with tempfile.TemporaryDirectory(prefix="sync_test_") as temp_dir:
        base = Path(temp_dir)
        source = base / "source"
        replica = base / "replica"
        log = base / "sync.log"

        source.mkdir()

        yield {
            "base": base,
            "source": source,
            "replica": replica,
            "log": log,
        }


def run_sync(*args: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(command, capture_output=True, text=True)


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr.strip()


def assert_failure(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode != 0


def assert_replica_file(replica: Path, relative_path: str, content: str) -> None:
    path = replica / relative_path
    assert path.exists()
    assert path.read_text() == content


def assert_replica_missing(replica: Path, relative_path: str) -> None:
    assert not (replica / relative_path).exists()


def test_basic_sync() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "file1.txt").write_text("hello")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_file(replica, "file1.txt", "hello")


def test_idempotent() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "file1.txt").write_text("hello")
        (source / "file2.txt").write_text("world")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_file(replica, "file1.txt", "hello")
        assert_replica_file(replica, "file2.txt", "world")


def test_modified_in_replica() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "file1.txt").write_text("hello")
        replica.mkdir(parents=True)
        (replica / "file1.txt").write_text("modified")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_file(replica, "file1.txt", "hello")


def test_extra_file_in_replica() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "file1.txt").write_text("hello")
        replica.mkdir(parents=True)
        (replica / "extra.txt").write_text("extra")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_missing(replica, "extra.txt")


def test_extra_directory_in_replica() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "file1.txt").write_text("hello")
        (replica / "extra_dir" / "nested").mkdir(parents=True)

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_missing(replica, "extra_dir")


def test_nested_directories() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "a" / "b").mkdir(parents=True)
        (source / "a" / "b" / "deep.txt").write_text("deep")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_file(replica, "a/b/deep.txt", "deep")


def test_empty_source() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        replica.mkdir(parents=True)
        (replica / "should_be_deleted.txt").write_text("bye")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_missing(replica, "should_be_deleted.txt")


def test_replica_does_not_exist() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        (source / "new_file.txt").write_text("created")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_success(result)
        assert_replica_file(replica, "new_file.txt", "created")


def test_source_does_not_exist() -> None:
    with sync_env() as env:
        source = env["source"] / "nonexistent"
        replica = env["replica"]
        log = env["log"]

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_failure(result)


def test_source_is_file() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        file_source = source / "new_file.txt"
        file_source.write_text("content")

        result = run_sync(str(file_source), str(replica), "0", "1", str(log))

        assert_failure(result)


def test_replica_is_file() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        replica.write_text("i am a file")

        result = run_sync(str(source), str(replica), "0", "1", str(log))

        assert_failure(result)


def test_zero_sync_count() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        result = run_sync(str(source), str(replica), "0", "0", str(log))

        assert_failure(result)


def test_invalid_interval() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        log = env["log"]

        result = run_sync(str(source), str(replica), "abc", "1", str(log))

        assert_failure(result)


def test_custom_log_path() -> None:
    with sync_env() as env:
        source = env["source"]
        replica = env["replica"]
        custom_log = env["base"] / "logs" / "subdir" / "custom.log"

        (source / "log_test.txt").write_text("logging")

        result = run_sync(str(source), str(replica), "0", "1", str(custom_log))

        assert_success(result)
        assert custom_log.exists()
        assert "Copied file" in custom_log.read_text()


def main() -> int:
    tests = [
        test_basic_sync,
        test_idempotent,
        test_modified_in_replica,
        test_extra_file_in_replica,
        test_extra_directory_in_replica,
        test_nested_directories,
        test_empty_source,
        test_replica_does_not_exist,
        test_source_does_not_exist,
        test_source_is_file,
        test_replica_is_file,
        test_zero_sync_count,
        test_invalid_interval,
        test_custom_log_path,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
        except AssertionError as exc:
            print(f"{test.__name__}... FAIL")
            if str(exc):
                print(f"  {exc}")
            failed += 1
        else:
            print(f"{test.__name__}... OK")
            passed += 1

    print(f"\n{passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
