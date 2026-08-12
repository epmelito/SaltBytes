import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from saltbytes.database import (
    complete_pipeline_run,
    initialize_database,
    insert_forecast_snapshot,
    insert_pipeline_run,
)

STARTED_AT = datetime(2026, 8, 3, 12, tzinfo=timezone.utc)
COMPLETED_AT = datetime(2026, 8, 3, 12, 5, tzinfo=timezone.utc)


def _bash_path() -> str:
    discovered = shutil.which("bash")
    if discovered:
        return discovered

    git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.is_file():
        return str(git_bash)

    pytest.skip("bash is required to exercise hosted ingestion")


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    path.chmod(0o755)


def _run_hosted_ingestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    failed_blob: str = "",
    failed_attempts: int = 0,
    missing_raw_reference: bool = False,
) -> tuple[subprocess.CompletedProcess[str], list[str], Path]:
    scripts_path = tmp_path / "scripts"
    commands_path = tmp_path / "commands"
    capture_path = tmp_path / "captured"
    scripts_path.mkdir()
    commands_path.mkdir()
    capture_path.mkdir()
    shutil.copy("scripts/hosted_ingestion.sh", scripts_path)
    shutil.copy("scripts/validate_hosted_database.py", scripts_path)

    database_path = tmp_path / "data/local/saltbytes.duckdb"
    database_path.parent.mkdir(parents=True)
    initialize_database(database_path)
    insert_pipeline_run(database_path, "run123", STARTED_AT)
    raw_file_paths = [
        "data/local/raw/run/a.json",
        "data/local/raw/run/b.json",
    ]
    if missing_raw_reference:
        raw_file_paths.append("data/local/raw/run/missing.json")
    for index, raw_file_path in enumerate(raw_file_paths):
        insert_forecast_snapshot(
            database_path,
            {
                "snapshot_id": f"snapshot-{index}",
                "run_id": "run123",
                "location_id": "test-location",
                "captured_at": STARTED_AT,
                "raw_file_path": raw_file_path,
                "model_selector": None,
                "request_latitude": None,
                "request_longitude": None,
                "returned_latitude": None,
                "returned_longitude": None,
            },
        )
    complete_pipeline_run(
        database_path,
        "run123",
        COMPLETED_AT,
        "success",
        len(raw_file_paths),
    )

    _write_executable(
        commands_path / "saltbytes",
        r"""#!/usr/bin/env bash
set -uo pipefail
mkdir -p data/local/raw/run
printf '{"snapshot": "a"}\n' > data/local/raw/run/a.json
printf '{"snapshot": "b"}\n' > data/local/raw/run/b.json
""",
    )
    _write_executable(
        commands_path / "sleep",
        r"""#!/usr/bin/env bash
exit 0
""",
    )
    _write_executable(
        commands_path / "az",
        r"""#!/usr/bin/env bash
set -uo pipefail

if [[ "${1:-}" == "storage" && "${2:-}" == "blob" && "${3:-}" == "exists" ]]; then
    printf 'false\n'
    exit 0
fi

blob_name=''
file_path=''
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --name)
            blob_name="$2"
            shift 2
            ;;
        --file)
            file_path="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

printf '%s\n' "$blob_name" >> "$AZ_UPLOAD_LOG"
attempt_file="$AZ_STATE_DIR/${blob_name//\//__}"
attempt=0
if [[ -f "$attempt_file" ]]; then
    attempt="$(<"$attempt_file")"
fi
((attempt += 1))
printf '%s\n' "$attempt" > "$attempt_file"

if [[ "$blob_name" == "$FAILED_BLOB" && "$attempt" -le "$FAILED_ATTEMPTS" ]]; then
    exit 1
fi

cp "$file_path" "$AZ_CAPTURE_DIR/${blob_name//\//__}"
""",
    )

    upload_log = tmp_path / "uploads.log"
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "storage-account")
    monkeypatch.setenv("AZURE_STORAGE_CONTAINER", "saltbytes-state")
    monkeypatch.setenv("AZ_UPLOAD_LOG", str(upload_log))
    monkeypatch.setenv("AZ_STATE_DIR", str(tmp_path / "attempts"))
    monkeypatch.setenv("AZ_CAPTURE_DIR", str(capture_path))
    monkeypatch.setenv("FAILED_BLOB", failed_blob)
    monkeypatch.setenv("FAILED_ATTEMPTS", str(failed_attempts))
    (tmp_path / "attempts").mkdir()

    environment = os.environ.copy()
    environment["PATH"] = str(commands_path) + os.pathsep + environment["PATH"]
    source_path = str(Path.cwd() / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        value
        for value in (source_path, environment.get("PYTHONPATH"))
        if value
    )
    result = subprocess.run(
        [_bash_path(), "scripts/hosted_ingestion.sh"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    uploads = upload_log.read_text(encoding="utf-8").splitlines()
    return result, uploads, capture_path


def test_successful_publication_replaces_canonical_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(tmp_path, monkeypatch)

    assert result.returncode == 0
    assert sorted(uploads[:-1]) == ["raw/run/a.json", "raw/run/b.json"]
    assert uploads[-1] == "state/saltbytes.duckdb"
    assert "raw publication totals: total=2 published=2 failed=0" in result.stdout
    assert "final hosted outcome: canonical state published" in result.stdout
    assert not any(path.name.startswith("recovery__") for path in capture_path.iterdir())


def test_partial_raw_failure_attempts_remaining_raw_and_preserves_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        failed_blob="raw/run/a.json",
        failed_attempts=3,
    )

    assert result.returncode == 1
    assert uploads.count("raw/run/a.json") == 3
    assert uploads.count("raw/run/b.json") == 1
    assert "state/saltbytes.duckdb" not in uploads
    assert "recovery/run123/saltbytes.duckdb" in uploads
    assert "recovery/run123/publication-failures.txt" in uploads
    assert "raw publication totals: total=2 published=1 failed=1" in result.stdout
    assert "recovery publication status: database=published manifest=published" in result.stdout
    assert "publication incomplete; canonical state unchanged" in result.stderr

    manifest = (
        capture_path / "recovery__run123__publication-failures.txt"
    ).read_text(encoding="utf-8")
    assert "canonical_database=not_attempted" in manifest
    assert "failed_raw_blob=raw/run/a.json" in manifest
    assert 'unpublished_raw_reference="data/local/raw/run/a.json"' in manifest


def test_failed_canonical_upload_is_bounded_and_preserves_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        failed_blob="state/saltbytes.duckdb",
        failed_attempts=3,
    )

    assert result.returncode == 1
    assert uploads.count("state/saltbytes.duckdb") == 3
    assert "recovery/run123/saltbytes.duckdb" in uploads
    assert "recovery/run123/publication-failures.txt" in uploads
    manifest = (
        capture_path / "recovery__run123__publication-failures.txt"
    ).read_text(encoding="utf-8")
    assert "raw_failed=0" in manifest
    assert "canonical_database=failed" in manifest


def test_missing_referenced_raw_file_blocks_canonical_and_records_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        missing_raw_reference=True,
    )

    assert result.returncode == 1
    assert "state/saltbytes.duckdb" not in uploads
    assert "recovery/run123/saltbytes.duckdb" in uploads
    assert "recovery/run123/publication-failures.txt" in uploads
    assert "raw reference verification: expected=3 verified=2 failed=1" in result.stderr
    assert "publication incomplete; canonical state unchanged" in result.stderr

    manifest = (
        capture_path / "recovery__run123__publication-failures.txt"
    ).read_text(encoding="utf-8")
    assert 'missing_raw_reference="data/local/raw/run/missing.json"' in manifest
