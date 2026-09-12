import json
from datetime import datetime, timezone

import pytest

from saltbytes.lifecycle_telemetry import (
    aggregate_active_inventory,
    aggregate_soft_deleted_snapshots,
    azure_lifecycle_record,
)

CUTOFF = datetime(2026, 6, 14, tzinfo=timezone.utc)


def test_active_inventory_aggregates_footprint_and_cleanup_candidates() -> None:
    inventory = aggregate_active_inventory(
        json.dumps(
            [
                {
                    "name": "raw/expired.json",
                    "properties": {
                        "contentLength": 25,
                        "lastModified": "2026-06-13T23:59:59Z",
                    },
                },
                {
                    "name": "raw/current.json",
                    "properties": {
                        "contentLength": 75,
                        "lastModified": "2026-06-14T00:00:00+00:00",
                    },
                },
            ]
        ),
        "raw/",
        CUTOFF,
    )

    assert inventory.active_count == 2
    assert inventory.active_payload_bytes == 100
    assert inventory.candidate_count == 1
    assert inventory.candidate_payload_bytes == 25
    assert [(item.name, item.payload_bytes) for item in inventory.candidates] == [
        ("raw/expired.json", 25)
    ]


def test_active_inventory_handles_zero_items() -> None:
    inventory = aggregate_active_inventory("[]", "recovery/", CUTOFF)

    assert inventory.active_count == 0
    assert inventory.active_payload_bytes == 0
    assert inventory.candidate_count == 0
    assert inventory.candidate_payload_bytes == 0
    assert inventory.candidates == ()


@pytest.mark.parametrize(
    "payload",
    (
        "not json",
        '[{"name":"state/saltbytes.duckdb","properties":'
        '{"contentLength":1,"lastModified":"2026-01-01T00:00:00Z"}}]',
        '[{"name":"raw/item","properties":'
        '{"contentLength":-1,"lastModified":"2026-01-01T00:00:00Z"}}]',
    ),
)
def test_active_inventory_rejects_unsafe_or_invalid_provider_data(payload: str) -> None:
    with pytest.raises(ValueError):
        aggregate_active_inventory(payload, "raw/", CUTOFF)


def test_soft_deleted_snapshot_aggregation_counts_only_canonical_overwrites() -> None:
    count, payload_bytes = aggregate_soft_deleted_snapshots(
        json.dumps(
            [
                {
                    "name": "state/saltbytes.duckdb",
                    "deleted": True,
                    "snapshot": "2026-09-11T12:00:00Z",
                    "properties": {"contentLength": 40},
                },
                {
                    "name": "state/saltbytes.duckdb",
                    "deleted": False,
                    "snapshot": None,
                    "properties": {"contentLength": 50},
                },
                {
                    "name": "state/other.duckdb",
                    "deleted": True,
                    "snapshot": "2026-09-11T12:00:00Z",
                    "properties": {"contentLength": 60},
                },
            ]
        ),
        "state/saltbytes.duckdb",
    )

    assert count == 1
    assert payload_bytes == 40


def test_azure_record_distinguishes_payload_metrics_and_unavailable_observation() -> None:
    record = azure_lifecycle_record(
        pipeline_run_id="run123",
        observed_at="2026-09-12T12:00:00Z",
        artifact_retention_days=90,
        cleanup_cutoff="2026-06-14T12:00:00Z",
        canonical_payload_status="available",
        canonical_payload_bytes=500,
        prefix_metrics={
            "raw/": ("available", (3, 300, 2, 200, 1, 75, 1, 125)),
            "recovery/": ("unavailable", (0, 0, 0, 0, 0, 0, 0, 0)),
        },
        soft_deleted_status="unavailable",
        soft_deleted_count=None,
        soft_deleted_payload_bytes=None,
    )

    assert record["schema"] == "saltbytes.storage-lifecycle"
    assert record["version"] == 1
    assert record["byte_measurement"] == "logical_payload_bytes_not_billed_capacity"
    assert record["canonical_duckdb"] == {
        "payload_bytes": 500,
        "status": "available",
    }
    assert record["prefixes"]["raw/"]["cleanup_candidates"] == {
        "count": 2,
        "payload_bytes": 200,
    }
    assert record["prefixes"]["raw/"]["successful_removals"] == {
        "count": 1,
        "payload_bytes": 75,
    }
    assert record["prefixes"]["raw/"]["failed_removals"] == {
        "count": 1,
        "payload_bytes": 125,
    }
    assert record["prefixes"]["raw/"]["active_before_cleanup"] == {
        "count": 3,
        "payload_bytes": 300,
    }
    assert record["prefixes"]["raw/"]["active_after_cleanup"] == {
        "count": 2,
        "payload_bytes": 225,
    }
    assert record["prefixes"]["recovery/"] == {
        "active_before_cleanup": None,
        "active_after_cleanup": None,
        "cleanup_candidates": None,
        "failed_removals": None,
        "status": "unavailable",
        "successful_removals": None,
    }
    assert record["canonical_soft_deleted_snapshots"] == {
        "count": None,
        "payload_bytes": None,
        "status": "unavailable",
    }
