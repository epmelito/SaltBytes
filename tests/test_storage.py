import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from forecast_ops.storage import write_raw_snapshot


def test_write_raw_snapshot_creates_immutable_json_file(tmp_path: Path) -> None:
    payload = {
        "latitude": 50.08,
        "longitude": 14.44,
        "hourly": {
            "time": ["2026-07-28T00:00"],
            "wind_speed_10m": [18.2],
        },
    }
    captured_at = datetime(2026, 7, 28, 10, 30, tzinfo=timezone.utc)

    metadata = write_raw_snapshot(
        payload=payload,
        location_id="prague",
        raw_data_path=tmp_path,
        run_id="run123",
        snapshot_id="snapshot123",
        captured_at=captured_at,
    )

    expected_path = (
        tmp_path
        / "2026"
        / "07"
        / "28"
        / "run123"
        / "prague_snapshot123.json"
    )

    assert Path(metadata["raw_file_path"]) == expected_path
    assert metadata["snapshot_id"] == "snapshot123"
    assert metadata["run_id"] == "run123"
    assert metadata["location_id"] == "prague"
    assert metadata["captured_at"] == captured_at
    assert json.loads(expected_path.read_text(encoding="utf-8")) == payload


def test_write_raw_snapshot_refuses_to_overwrite_existing_file(
    tmp_path: Path,
) -> None:
    captured_at = datetime(2026, 7, 28, 10, 30, tzinfo=timezone.utc)

    arguments = {
        "payload": {"hourly": {"time": []}},
        "location_id": "prague",
        "raw_data_path": tmp_path,
        "run_id": "run123",
        "snapshot_id": "snapshot123",
        "captured_at": captured_at,
    }

    write_raw_snapshot(**arguments)

    with pytest.raises(FileExistsError):
        write_raw_snapshot(**arguments)


def test_write_raw_snapshot_requires_timezone_aware_timestamp(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="captured_at must include timezone information",
    ):
        write_raw_snapshot(
            payload={},
            location_id="prague",
            raw_data_path=tmp_path,
            run_id="run123",
            captured_at=datetime(2026, 7, 28, 10, 30),
        )


@pytest.mark.parametrize(
    ("field_name", "location_id", "run_id", "snapshot_id"),
    [
        ("location_id", "../prague", "run123", "snapshot123"),
        ("run_id", "prague", "../run123", "snapshot123"),
        ("snapshot_id", "prague", "run123", "../snapshot123"),
    ],
)
def test_write_raw_snapshot_rejects_unsafe_path_components(
    tmp_path: Path,
    field_name: str,
    location_id: str,
    run_id: str,
    snapshot_id: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        write_raw_snapshot(
            payload={},
            location_id=location_id,
            raw_data_path=tmp_path,
            run_id=run_id,
            snapshot_id=snapshot_id,
        )
