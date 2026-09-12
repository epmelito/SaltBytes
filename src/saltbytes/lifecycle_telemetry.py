import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from saltbytes.database import EnvironmentalRetentionResult

TELEMETRY_SCHEMA = "saltbytes.storage-lifecycle"
TELEMETRY_VERSION = 1


@dataclass(frozen=True)
class BlobCandidate:
    name: str
    payload_bytes: int


@dataclass(frozen=True)
class BlobInventory:
    active_count: int
    active_payload_bytes: int
    candidate_count: int
    candidate_payload_bytes: int
    candidates: tuple[BlobCandidate, ...]


def _utc_text(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def encode_telemetry(record: dict[str, Any]) -> str:
    return json.dumps(record, separators=(",", ":"), sort_keys=True)


def database_retention_record(
    result: EnvironmentalRetentionResult,
) -> dict[str, Any]:
    return {
        "schema": TELEMETRY_SCHEMA,
        "version": TELEMETRY_VERSION,
        "record_type": "database_retention",
        "observed_at": _utc_text(result.observed_at),
        "pipeline_run_id": result.pipeline_run_id,
        "retention_days": {
            "normalized": result.normalized_retention_days,
            "metadata": result.metadata_retention_days,
        },
        "protected_successful_run_id": result.protected_run_id,
        "rows": {
            "normalized": {
                "removed": result.normalized_rows_removed,
                "retained": result.normalized_rows_retained,
            },
            "metadata": {
                "removed": result.metadata_rows_removed,
                "retained": result.metadata_rows_retained,
            },
        },
        "duckdb_payload_bytes": {
            "before_retention": result.database_size_before,
            "after_checkpoint": result.database_size_after,
        },
    }


def _parse_utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field_name} must be a valid timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _payload_bytes(blob: dict[str, Any]) -> int:
    properties = blob.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("blob properties must be an object")
    value = properties.get("contentLength")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("blob properties.contentLength must be a nonnegative integer")
    return value


def _blob_list(payload: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError("blob inventory must be valid JSON") from error
    if not isinstance(parsed, list) or any(not isinstance(item, dict) for item in parsed):
        raise ValueError("blob inventory must be a JSON array of objects")
    return parsed


def aggregate_active_inventory(
    payload: str,
    prefix: str,
    cutoff: datetime,
) -> BlobInventory:
    if not prefix or prefix == "state/" or not prefix.endswith("/"):
        raise ValueError("lifecycle prefix is invalid")
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cleanup cutoff must include a timezone")

    active_count = 0
    active_payload_bytes = 0
    candidates: list[BlobCandidate] = []
    for blob in _blob_list(payload):
        name = blob.get("name")
        if not isinstance(name, str) or not name.startswith(prefix) or "\0" in name:
            raise ValueError(f"blob inventory contains an unsafe name for {prefix}")
        if blob.get("deleted") is True or blob.get("snapshot") is not None:
            raise ValueError("active blob inventory contains a deleted blob or snapshot")
        payload_bytes = _payload_bytes(blob)
        last_modified = _parse_utc(
            blob.get("properties", {}).get("lastModified"),
            "blob properties.lastModified",
        )
        active_count += 1
        active_payload_bytes += payload_bytes
        if last_modified < cutoff:
            candidates.append(BlobCandidate(name, payload_bytes))

    return BlobInventory(
        active_count=active_count,
        active_payload_bytes=active_payload_bytes,
        candidate_count=len(candidates),
        candidate_payload_bytes=sum(item.payload_bytes for item in candidates),
        candidates=tuple(candidates),
    )


def aggregate_soft_deleted_snapshots(payload: str, blob_name: str) -> tuple[int, int]:
    count = 0
    payload_bytes = 0
    for blob in _blob_list(payload):
        if (
            blob.get("name") == blob_name
            and blob.get("deleted") is True
            and isinstance(blob.get("snapshot"), str)
            and blob["snapshot"]
        ):
            count += 1
            payload_bytes += _payload_bytes(blob)
    return count, payload_bytes


def _metric_record(values: tuple[int, ...]) -> dict[str, dict[str, int]]:
    if values[4] > values[0] or values[5] > values[1]:
        raise ValueError("successful removals cannot exceed active inventory")
    return {
        "active_before_cleanup": {
            "count": values[0],
            "payload_bytes": values[1],
        },
        "cleanup_candidates": {"count": values[2], "payload_bytes": values[3]},
        "successful_removals": {"count": values[4], "payload_bytes": values[5]},
        "failed_removals": {"count": values[6], "payload_bytes": values[7]},
        "active_after_cleanup": {
            "count": values[0] - values[4],
            "payload_bytes": values[1] - values[5],
        },
    }


def azure_lifecycle_record(
    *,
    pipeline_run_id: str,
    observed_at: str,
    artifact_retention_days: int,
    cleanup_cutoff: str,
    canonical_payload_status: str,
    canonical_payload_bytes: int | None,
    prefix_metrics: dict[str, tuple[str, tuple[int, ...]]],
    soft_deleted_status: str,
    soft_deleted_count: int | None,
    soft_deleted_payload_bytes: int | None,
) -> dict[str, Any]:
    prefixes: dict[str, Any] = {}
    for prefix in ("raw/", "recovery/"):
        status, values = prefix_metrics[prefix]
        metrics = _metric_record(values)
        if status == "unavailable":
            metrics = {name: None for name in metrics}
        prefixes[prefix] = {
            "status": status,
            **metrics,
        }
    return {
        "schema": TELEMETRY_SCHEMA,
        "version": TELEMETRY_VERSION,
        "record_type": "hosted_storage_lifecycle",
        "observed_at": observed_at,
        "pipeline_run_id": pipeline_run_id,
        "artifact_retention_days": artifact_retention_days,
        "cleanup_cutoff": cleanup_cutoff,
        "byte_measurement": "logical_payload_bytes_not_billed_capacity",
        "canonical_duckdb": {
            "status": canonical_payload_status,
            "payload_bytes": canonical_payload_bytes,
        },
        "prefixes": prefixes,
        "canonical_soft_deleted_snapshots": {
            "status": soft_deleted_status,
            "count": soft_deleted_count,
            "payload_bytes": soft_deleted_payload_bytes,
        },
    }


def _parse_metrics(value: str) -> tuple[int, ...]:
    try:
        parsed = tuple(int(part) for part in value.split(","))
    except ValueError as error:
        raise ValueError("prefix metrics must contain integers") from error
    if len(parsed) != 8 or any(item < 0 for item in parsed):
        raise ValueError("prefix metrics must contain eight nonnegative integers")
    return parsed


def _write_candidates(path: Path, candidates: tuple[BlobCandidate, ...]) -> None:
    with path.open("wb") as output:
        for candidate in candidates:
            output.write(candidate.name.encode("utf-8"))
            output.write(b"\0")
            output.write(str(candidate.payload_bytes).encode("ascii"))
            output.write(b"\0")


def _parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("prefix")
    inventory.add_argument("cutoff")
    inventory.add_argument("candidate_output", type=Path)

    snapshots = subparsers.add_parser("soft-deleted-snapshots")
    snapshots.add_argument("blob_name")

    azure = subparsers.add_parser("azure-record")
    azure.add_argument("--pipeline-run-id", required=True)
    azure.add_argument("--observed-at", required=True)
    azure.add_argument("--artifact-retention-days", required=True, type=int)
    azure.add_argument("--cleanup-cutoff", required=True)
    azure.add_argument(
        "--canonical-payload-status",
        choices=("available", "unavailable"),
        required=True,
    )
    azure.add_argument("--canonical-payload-bytes", type=int)
    azure.add_argument("--raw-status", choices=("available", "unavailable"), required=True)
    azure.add_argument("--raw-metrics", required=True)
    azure.add_argument("--recovery-status", choices=("available", "unavailable"), required=True)
    azure.add_argument("--recovery-metrics", required=True)
    azure.add_argument(
        "--soft-deleted-status",
        choices=("available", "unavailable"),
        required=True,
    )
    azure.add_argument("--soft-deleted-count", type=int)
    azure.add_argument("--soft-deleted-payload-bytes", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse_arguments(argv or sys.argv[1:])
    try:
        if arguments.command == "inventory":
            inventory = aggregate_active_inventory(
                sys.stdin.read(),
                arguments.prefix,
                _parse_utc(arguments.cutoff, "cleanup cutoff"),
            )
            _write_candidates(arguments.candidate_output, inventory.candidates)
            print(
                "\t".join(
                    str(value)
                    for value in (
                        inventory.active_count,
                        inventory.active_payload_bytes,
                        inventory.candidate_count,
                        inventory.candidate_payload_bytes,
                    )
                )
            )
            return 0

        if arguments.command == "soft-deleted-snapshots":
            count, payload_bytes = aggregate_soft_deleted_snapshots(
                sys.stdin.read(), arguments.blob_name
            )
            print(f"{count}\t{payload_bytes}")
            return 0

        canonical_payload_bytes = arguments.canonical_payload_bytes
        if arguments.canonical_payload_status == "available" and canonical_payload_bytes is None:
            raise ValueError("available canonical payload telemetry requires payload bytes")
        if arguments.canonical_payload_status == "unavailable":
            canonical_payload_bytes = None
        soft_values = (arguments.soft_deleted_count, arguments.soft_deleted_payload_bytes)
        if arguments.soft_deleted_status == "available" and None in soft_values:
            raise ValueError("available soft-deleted metrics require count and payload bytes")
        if arguments.soft_deleted_status == "unavailable":
            soft_values = (None, None)
        record = azure_lifecycle_record(
            pipeline_run_id=arguments.pipeline_run_id,
            observed_at=arguments.observed_at,
            artifact_retention_days=arguments.artifact_retention_days,
            cleanup_cutoff=arguments.cleanup_cutoff,
            canonical_payload_status=arguments.canonical_payload_status,
            canonical_payload_bytes=canonical_payload_bytes,
            prefix_metrics={
                "raw/": (arguments.raw_status, _parse_metrics(arguments.raw_metrics)),
                "recovery/": (
                    arguments.recovery_status,
                    _parse_metrics(arguments.recovery_metrics),
                ),
            },
            soft_deleted_status=arguments.soft_deleted_status,
            soft_deleted_count=soft_values[0],
            soft_deleted_payload_bytes=soft_values[1],
        )
        print(encode_telemetry(record))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"storage lifecycle telemetry failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
