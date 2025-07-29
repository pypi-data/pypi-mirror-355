"""Shard tests to support parallelism across multiple machines."""

import hashlib
import warnings
from typing import Iterable, List, Sequence
import xml.etree.ElementTree as ET

from _pytest import junitxml
from _pytest import nodes  # for type checking only
from pytest import Item


def _shard_by_duration(items: List[dict], num_bins: int):
    items.sort(reverse=True, key=lambda x: x["time"])

    bin_loads = [0] * num_bins

    bin_assignments = []
    for item in items:
        min_load_bin = min(range(num_bins), key=lambda i: bin_loads[i])

        bin_assignments.append(min_load_bin)
        bin_loads[min_load_bin] += item["time"]

    return bin_assignments


def positive_int(x) -> int:
    x = int(x)
    if x < 0:
        raise ValueError(f"Argument {x} must be positive")
    return x


def pytest_addoption(parser):
    """Add pytest-shard specific configuration parameters."""
    group = parser.getgroup("shard")
    group.addoption(
        "--shard-id",
        dest="shard_id",
        type=positive_int,
        default=0,
        help="Number of this shard.",
    )
    group.addoption(
        "--num-shards",
        dest="num_shards",
        type=positive_int,
        default=1,
        help="Total number of shards.",
    )
    group.addoption(
        "--shard-by-duration",
        dest="shard_by_duration",
        action="store_true",
        default=False,
        help="Whether to shard by duration or not.",
    )


def pytest_report_collectionfinish(config, items: Sequence[nodes.Node]) -> str:
    """Log how many and, if verbose, which items are tested in this shard."""
    msg = f"Running {len(items)} items in this shard"
    if config.option.verbose > 0 and config.getoption("num_shards") > 1:
        msg += ": " + ", ".join([item.nodeid for item in items])
    return msg


def sha256hash(x: str) -> int:
    return int.from_bytes(hashlib.sha256(x.encode()).digest(), "little")


def duration_shard(items: Iterable[Item], num_shards: int) -> List[int]:
    # Create a mapping from test address to item for quick lookup
    item_address = [junitxml.mangle_test_address(i.nodeid) for i in items]
    items_list = list(items)

    # Read data from durations.xml
    root = ET.parse("durations.xml").getroot()
    xml_data = []
    for e in root.findall("*/testcase"):
        xml_data.append(e.attrib)

    # Convert time to float
    for d in xml_data:
        d["time"] = float(d["time"])

    # Track tests in current suite that aren't in durations.xml
    tests_in_suite = {
        tuple(junitxml.mangle_test_address(i.nodeid)) for i in items_list
    }
    tests_in_xml = {(d["classname"], d["name"]) for d in xml_data}

    # Find tests missing from either side
    missing_from_xml = tests_in_suite - tests_in_xml
    missing_from_suite = tests_in_xml - tests_in_suite

    # Report warnings about missing tests
    if missing_from_xml:
        warnings.warn(
            f"Found {len(missing_from_xml)} tests in test suite that are missing from durations.xml. "
            f"These will be distributed in round-robin fashion."
        )

    if missing_from_suite:
        warnings.warn(
            f"Found {len(missing_from_suite)} tests in durations.xml that are missing from the test suite. "
            f"These will be ignored."
        )

    # Filter data to include only tests that exist in the current test suite
    matched_data = []
    for d in xml_data:
        test_key = (d["classname"], d["name"])
        if test_key in tests_in_suite:
            matched_data.append(d)

    # Sort matched data by their position in items list
    def get_index(item_data):
        test_key = [item_data["classname"], item_data["name"]]
        try:
            return item_address.index(test_key)
        except ValueError:
            # This shouldn't happen since we filtered above, but just in case
            return float("inf")

    matched_data.sort(key=get_index)

    # Get shard assignments for matched tests
    shard_ids = [0] * len(items_list)
    if matched_data:
        duration_shard_ids = _shard_by_duration(matched_data, num_shards)

        # Map duration_shard_ids back to original items
        for i, d in enumerate(matched_data):
            test_key = [d["classname"], d["name"]]
            try:
                item_idx = item_address.index(test_key)
                shard_ids[item_idx] = duration_shard_ids[i]
            except ValueError:
                # Skip items that are in xml but not in test suite (shouldn't happen due to filtering)
                pass

    # Assign missing tests round-robin
    current_shard = 0
    for i, item in enumerate(items_list):
        test_key = tuple(junitxml.mangle_test_address(item.nodeid))
        if test_key in missing_from_xml:
            shard_ids[i] = current_shard
            current_shard = (current_shard + 1) % num_shards

    return shard_ids


def filter_items_by_shard(
    items: Iterable[Item],
    shard_id: int,
    num_shards: int,
    shard_by_duration: bool,
) -> Sequence[Item]:
    """Computes `items` that should be tested in `shard_id` out of `num_shards` total shards."""
    items_list = list(items)
    if shard_by_duration:
        try:
            shards = duration_shard(items_list, num_shards)
        except Exception as e:
            warnings.warn(
                f"Error in duration sharding: {str(e)}. Falling back to hash sharding."
            )
            shards = [
                sha256hash(item.nodeid) % num_shards for item in items_list
            ]
    else:
        shards = [sha256hash(item.nodeid) % num_shards for item in items_list]

    new_items = []
    for shard, item in zip(shards, items_list):
        if shard == shard_id:
            new_items.append(item)
    return new_items


def pytest_collection_modifyitems(config, items: List[Item]):
    """Mutate the collection to consist of just items to be tested in this shard."""
    shard_id = config.getoption("shard_id")
    shard_total = config.getoption("num_shards")
    shard_by_duration = config.getoption("shard_by_duration")
    if shard_id >= shard_total:
        raise ValueError(
            "shard_num = f{shard_num} must be less than shard_total = f{shard_total}"
        )

    items[:] = filter_items_by_shard(
        items, shard_id, shard_total, shard_by_duration
    )
