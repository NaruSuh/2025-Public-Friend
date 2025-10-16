"""Concurrency tests for file locking."""

import pytest
import json
import time
import sys
from pathlib import Path
from threading import Thread

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_utils import _load_json, _atomic_write_json, _get_lock


def test_concurrent_writes_no_corruption(tmp_path):
    """Test that concurrent writes don't corrupt JSON files."""
    test_file = tmp_path / "test.json"
    errors = []

    def writer(value):
        try:
            for i in range(10):
                data = {"value": value, "iteration": i}
                lock = _get_lock(test_file)
                with lock:
                    _atomic_write_json(test_file, data)
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)

    threads = [Thread(target=writer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have no errors
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Final file should be valid JSON (not corrupted)
    with test_file.open() as f:
        data = json.load(f)
    assert "value" in data
    assert isinstance(data["value"], int)
    assert "iteration" in data


def test_concurrent_read_write_consistency(tmp_path):
    """Test that concurrent reads always get valid data."""
    test_file = tmp_path / "test.json"
    _atomic_write_json(test_file, {"counter": 0})

    errors = []
    invalid_reads = []

    def reader():
        try:
            for _ in range(20):
                data = _load_json(test_file, {"counter": -1})
                if "counter" not in data:
                    invalid_reads.append("Missing 'counter' key")
                elif not isinstance(data["counter"], int):
                    invalid_reads.append(f"Invalid counter type: {type(data['counter'])}")
                time.sleep(0.005)
        except Exception as e:
            errors.append(e)

    def writer():
        try:
            for i in range(20):
                lock = _get_lock(test_file)
                with lock:
                    _atomic_write_json(test_file, {"counter": i})
                time.sleep(0.005)
        except Exception as e:
            errors.append(e)

    threads = [
        Thread(target=reader),
        Thread(target=reader),
        Thread(target=writer)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(invalid_reads) == 0, f"Invalid reads: {invalid_reads}"


def test_load_json_creates_default_if_missing(tmp_path):
    """Test that _load_json creates file with default value if it doesn't exist."""
    test_file = tmp_path / "new_file.json"
    default_value = {"test": "default"}

    result = _load_json(test_file, default_value)

    assert result == default_value
    assert test_file.exists()

    # Verify file content
    with test_file.open() as f:
        data = json.load(f)
    assert data == default_value


def test_load_json_handles_corrupted_file(tmp_path):
    """Test that _load_json recovers from corrupted JSON files."""
    test_file = tmp_path / "corrupted.json"
    test_file.write_text("{ invalid json }", encoding="utf-8")

    default_value = {"recovered": True}
    result = _load_json(test_file, default_value)

    # Should return default and fix the file
    assert result == default_value

    # Verify file was repaired
    with test_file.open() as f:
        data = json.load(f)
    assert data == default_value


def test_atomic_write_prevents_partial_reads(tmp_path):
    """Test that atomic writes prevent readers from seeing partial data."""
    test_file = tmp_path / "atomic_test.json"
    initial_data = {"status": "initial"}
    _atomic_write_json(test_file, initial_data)

    partial_reads = []
    errors = []

    def reader():
        try:
            for _ in range(50):
                data = _load_json(test_file, {})
                # Should always have exactly one key
                if len(data) != 1:
                    partial_reads.append(f"Unexpected keys: {list(data.keys())}")
                if "status" not in data:
                    partial_reads.append("Missing 'status' key")
                time.sleep(0.001)
        except Exception as e:
            errors.append(e)

    def writer():
        try:
            for i in range(25):
                # Write increasingly large data
                large_data = {"status": f"iteration_{i}_" + "x" * 1000}
                lock = _get_lock(test_file)
                with lock:
                    _atomic_write_json(test_file, large_data)
                time.sleep(0.002)
        except Exception as e:
            errors.append(e)

    threads = [
        Thread(target=reader),
        Thread(target=reader),
        Thread(target=writer)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"
    assert len(partial_reads) == 0, f"Partial reads detected: {partial_reads}"


def test_lock_timeout_returns_cached_data(tmp_path):
    """Test that lock timeout falls back to cached data (RF-001 fix)."""
    test_file = tmp_path / "timeout_test.json"
    initial_data = {"cached": "value"}
    _atomic_write_json(test_file, initial_data)

    # First read to populate cache
    result1 = _load_json(test_file, {})
    assert result1 == initial_data

    # Acquire lock in main thread and hold it
    lock = _get_lock(test_file)
    lock.acquire()

    try:
        # Try to read while lock is held - should timeout and return cached value
        result2 = _load_json(test_file, {"default": "fallback"})

        # Should return cached data, not default
        assert result2 == initial_data, "Should return cached data on timeout, not default"

    finally:
        lock.release()


def test_multiple_files_independent_locks(tmp_path):
    """Test that different files use independent locks."""
    file1 = tmp_path / "file1.json"
    file2 = tmp_path / "file2.json"

    errors = []

    def writer_file1():
        try:
            for i in range(20):
                lock = _get_lock(file1)
                with lock:
                    _atomic_write_json(file1, {"file": 1, "count": i})
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)

    def writer_file2():
        try:
            for i in range(20):
                lock = _get_lock(file2)
                with lock:
                    _atomic_write_json(file2, {"file": 2, "count": i})
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)

    threads = [Thread(target=writer_file1), Thread(target=writer_file2)]
    start_time = time.time()

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    assert len(errors) == 0, f"Errors: {errors}"
    # Should complete in ~0.2s if locks are independent, ~0.4s if serialized
    assert elapsed < 0.3, f"Locks may not be independent (took {elapsed:.2f}s)"


def test_lock_released_on_exception(tmp_path):
    """Test that locks are properly released even when exceptions occur."""
    test_file = tmp_path / "exception_test.json"

    class CustomException(Exception):
        pass

    def failing_operation():
        lock = _get_lock(test_file)
        with lock:
            raise CustomException("Simulated error")

    # First attempt should fail
    with pytest.raises(CustomException):
        failing_operation()

    # Second attempt should succeed (lock should be released)
    lock = _get_lock(test_file)
    acquired = lock.acquire(timeout=1)
    assert acquired, "Lock was not released after exception"
    lock.release()
