import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

_VALID_PATH_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


# generate identifiers without relying on timestamps for uniqueness
def create_run_id() -> str:
    return uuid4().hex


def create_snapshot_id() -> str:
    return uuid4().hex


# prevent identifiers from escaping the configured raw data directory
def _validate_path_component(value: str, field_name: str) -> None:
    if not _VALID_PATH_COMPONENT.fullmatch(value):
        raise ValueError(f"{field_name} contains invalid characters: {value}")


# write one immutable api response and return its snapshot metadata
def write_raw_snapshot(
    payload: dict[str, Any],
    location_id: str,
    raw_data_path: Path | str,
    run_id: str,
    run_started_at: datetime,
    snapshot_id: str | None = None,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    _validate_path_component(location_id, "location_id")
    _validate_path_component(run_id, "run_id")

    snapshot_id = snapshot_id or create_snapshot_id()
    _validate_path_component(snapshot_id, "snapshot_id")

    captured_at = captured_at or datetime.now(timezone.utc)

    for field_name, timestamp in (
        ("captured_at", captured_at),
        ("run_started_at", run_started_at),
    ):
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError(f"{field_name} must include timezone information")

    run_started_at_utc = run_started_at.astimezone(timezone.utc)
    run_directory = f"{run_started_at_utc.strftime('%H%M%SZ')}_{run_id}"

    raw_directory = (
        Path(raw_data_path)
        / run_started_at_utc.strftime("%Y")
        / run_started_at_utc.strftime("%m")
        / run_started_at_utc.strftime("%d")
        / run_directory
    )
    raw_directory.mkdir(parents=True, exist_ok=True)

    raw_file_path = raw_directory / f"{location_id}_{snapshot_id}.json"

    # exclusive creation prevents an existing snapshot from being overwritten
    with raw_file_path.open("x", encoding="utf-8") as raw_file:
        json.dump(payload, raw_file, indent=2, sort_keys=True)
        raw_file.write("\n")

    return {
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "location_id": location_id,
        "captured_at": captured_at,
        "raw_file_path": str(raw_file_path),
    }