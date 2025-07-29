"""Test pytest_shard.pytest_shard."""

import collections
import itertools
import os
import tempfile
import warnings
from unittest import mock
import xml.etree.ElementTree as ET

import hypothesis
from hypothesis import strategies
import pytest

from pytest_shard import pytest_shard


@hypothesis.given(strategies.integers(min_value=0))
def test_positive_int_with_pos(x):
    assert pytest_shard.positive_int(x) == x
    assert pytest_shard.positive_int(str(x)) == x


@hypothesis.given(strategies.integers(max_value=-1))
def test_positive_int_with_neg(x):
    with pytest.raises(ValueError):
        pytest_shard.positive_int(x)
    with pytest.raises(ValueError):
        pytest_shard.positive_int(str(x))


def test_positive_int_with_non_num():
    invalid = ["foobar", "x1", "1x"]
    for s in invalid:
        with pytest.raises(ValueError):
            pytest_shard.positive_int(s)


@hypothesis.given(strategies.text())
def test_sha256hash_deterministic(s):
    x = pytest_shard.sha256hash(s)
    y = pytest_shard.sha256hash(s)
    assert x == y
    assert isinstance(x, int)


@hypothesis.given(strategies.text(), strategies.text())
def test_sha256hash_no_clash(s1, s2):
    if s1 != s2:
        assert pytest_shard.sha256hash(s1) != pytest_shard.sha256hash(s2)


MockItem = collections.namedtuple("MockItem", "nodeid")


@hypothesis.given(
    names=strategies.lists(strategies.text(), unique=True),
    num_shards=strategies.integers(min_value=1, max_value=500),
)
def test_filter_items_by_shard(names, num_shards):
    items = [MockItem(name) for name in names]

    filtered = [
        pytest_shard.filter_items_by_shard(
            items, shard_id=i, num_shards=num_shards, shard_by_duration=False
        )
        for i in range(num_shards)
    ]
    all_filtered = list(itertools.chain(*filtered))
    assert len(all_filtered) == len(items)
    assert set(all_filtered) == set(items)


def create_temp_durations_xml(testcases):
    """Create a temporary durations.xml file with the given testcases.

    Args:
        testcases: List of (classname, name, time) tuples

    Returns:
        Path to the temporary file
    """
    root = ET.Element("testsuites")
    testsuite = ET.SubElement(root, "testsuite", name="pytest")

    for classname, name, time in testcases:
        ET.SubElement(
            testsuite,
            "testcase",
            classname=classname,
            name=name,
            time=str(time),
        )

    tree = ET.ElementTree(root)
    fd, path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    tree.write(path)
    return path


def test_duration_shard_with_missing_tests():
    """Test that duration_shard handles tests missing from durations.xml."""
    # Create items that will be in test suite
    test_items = [
        MockItem("tests/test_a.py::test_1"),
        MockItem("tests/test_a.py::test_2"),
        MockItem(
            "tests/test_b.py::test_3"
        ),  # This one won't be in durations.xml
    ]

    # Create a temporary durations.xml file with only the first two tests
    xml_testcases = [
        ("tests.test_a", "test_1", 0.5),
        ("tests.test_a", "test_2", 0.3),
        ("tests.test_c", "test_4", 0.1),  # This one won't be in test suite
    ]

    temp_path = create_temp_durations_xml(xml_testcases)
    try:
        # Mock ET.parse to use our temporary file
        with mock.patch(
            "xml.etree.ElementTree.parse", return_value=ET.parse(temp_path)
        ):
            # Capture warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                # Run duration_shard
                shards = pytest_shard.duration_shard(test_items, num_shards=2)

                # Verify we got a shard assignment for each test
                assert len(shards) == len(test_items)

                # Verify warnings were emitted
                assert len(w) == 2
                assert "missing from durations.xml" in str(w[0].message)
                assert "missing from the test suite" in str(w[1].message)
    finally:
        os.unlink(temp_path)


def test_filter_items_by_shard_with_duration_error():
    """Test that filter_items_by_shard handles errors in duration_shard gracefully."""
    items = [MockItem(f"test_{i}") for i in range(10)]

    # Mock duration_shard to raise an exception
    with mock.patch(
        "pytest_shard.pytest_shard.duration_shard",
        side_effect=Exception("Test error"),
    ):
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Run filter_items_by_shard
            filtered = pytest_shard.filter_items_by_shard(
                items, shard_id=0, num_shards=2, shard_by_duration=True
            )

            # Verify we still got filtered items using the fallback mechanism
            assert len(filtered) > 0

            # Verify warning was emitted
            assert len(w) == 1
            assert "Error in duration sharding" in str(w[0].message)
            assert "Falling back to hash sharding" in str(w[0].message)


def test_round_robin_distribution():
    """Test that tests missing from durations.xml are distributed in round-robin fashion."""
    # Create test items that won't be in durations.xml
    test_items = [MockItem(f"tests/test_x.py::test_{i}") for i in range(10)]

    # Create an empty durations.xml
    temp_path = create_temp_durations_xml([])
    try:
        # Mock ET.parse to use our temporary file
        with mock.patch(
            "xml.etree.ElementTree.parse", return_value=ET.parse(temp_path)
        ):
            # Run duration_shard
            shards = pytest_shard.duration_shard(test_items, num_shards=3)

            # Verify we got a shard assignment for each test
            assert len(shards) == len(test_items)

            # Count tests per shard
            shard_counts = [0, 0, 0]
            for shard_id in shards:
                shard_counts[shard_id] += 1

            # Verify that tests are distributed approximately evenly
            # For 10 tests and 3 shards, we should have 3-4 tests per shard
            assert all(3 <= count <= 4 for count in shard_counts)

            # Verify the round-robin pattern (should go 0,1,2,0,1,2,...)
            expected_pattern = [i % 3 for i in range(10)]
            assert shards == expected_pattern
    finally:
        os.unlink(temp_path)
