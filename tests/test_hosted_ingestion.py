import json
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
    observation_failure_output: str = "",
    raw_blobs_json: str = "[]",
    recovery_blobs_json: str = "[]",
    fallback_raw_blobs: str = "",
    fallback_recovery_blobs: str = "",
    fallback_listing_failure_prefix: str = "",
    soft_deleted_blobs_json: str = "[]",
    soft_deleted_listing_failure: bool = False,
    remove_canonical_after_upload: bool = False,
    cleanup_failed_blob: str = "",
    retention_failure: bool = False,
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
printf 'saltbytes:%s\n' "$*" >> "$HOSTED_TRACE_LOG"
if [[ "${1:-}" == "observations" && -n "${OBSERVATION_FAILURE_OUTPUT:-}" ]]; then
    printf '%s\n' "$OBSERVATION_FAILURE_OUTPUT" >&2
    exit 1
fi
if [[ "${1:-}" == "retention" ]]; then
    if [[ "$RETENTION_FAILURE" == "true" ]]; then
        printf 'controlled retention failure\n' >&2
        exit 1
    fi
    printf '%s\n' \
        '{"record_type":"database_retention","schema":"saltbytes.storage-lifecycle","version":1}'
    exit 0
fi
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
prefix=''
num_results=''
query=''
include=''
operation="${3:-}"
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
        --prefix)
            prefix="$2"
            shift 2
            ;;
        --num-results)
            num_results="$2"
            shift 2
            ;;
        --query)
            query="$2"
            shift 2
            ;;
        --include)
            include="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [[ "$operation" == "list" ]]; then
    printf 'az:list:%s:num-results=%s:query=%s:include=%s\n' \
        "$prefix" "$num_results" "$query" "$include" >> "$HOSTED_TRACE_LOG"
    if [[ -n "$query" ]]; then
        if [[ "$prefix" == "$FALLBACK_LISTING_FAILURE_PREFIX" ]]; then
            exit 1
        elif [[ "$prefix" == "raw/" ]]; then
            printf '%s\n' "$FALLBACK_RAW_BLOBS"
        else
            printf '%s\n' "$FALLBACK_RECOVERY_BLOBS"
        fi
    elif [[ "$prefix" == "state/saltbytes.duckdb" ]]; then
        if [[ "$SOFT_DELETED_LISTING_FAILURE" == "true" ]]; then
            exit 1
        fi
        printf '%s\n' "$SOFT_DELETED_BLOBS_JSON"
    elif [[ "$prefix" == "raw/" ]]; then
        printf '%s\n' "$RAW_BLOBS_JSON"
    else
        printf '%s\n' "$RECOVERY_BLOBS_JSON"
    fi
    exit 0
fi

if [[ "$operation" == "delete" ]]; then
    printf 'az:delete:%s\n' "$blob_name" >> "$HOSTED_TRACE_LOG"
    if [[ "$blob_name" == "$CLEANUP_FAILED_BLOB" ]]; then
        exit 1
    fi
    exit 0
fi

printf 'az:upload:%s\n' "$blob_name" >> "$HOSTED_TRACE_LOG"
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
if [[ "$blob_name" == "state/saltbytes.duckdb" && \
    "$REMOVE_CANONICAL_AFTER_UPLOAD" == "true" ]]; then
    rm -f -- "$file_path"
fi
""",
    )

    upload_log = tmp_path / "uploads.log"
    upload_log.touch()
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "storage-account")
    monkeypatch.setenv("AZURE_STORAGE_CONTAINER", "saltbytes-state")
    monkeypatch.setenv("AZ_UPLOAD_LOG", str(upload_log))
    monkeypatch.setenv("AZ_STATE_DIR", str(tmp_path / "attempts"))
    monkeypatch.setenv("AZ_CAPTURE_DIR", str(capture_path))
    monkeypatch.setenv("FAILED_BLOB", failed_blob)
    monkeypatch.setenv("FAILED_ATTEMPTS", str(failed_attempts))
    monkeypatch.setenv("OBSERVATION_FAILURE_OUTPUT", observation_failure_output)
    monkeypatch.setenv("RAW_BLOBS_JSON", raw_blobs_json)
    monkeypatch.setenv("RECOVERY_BLOBS_JSON", recovery_blobs_json)
    monkeypatch.setenv("FALLBACK_RAW_BLOBS", fallback_raw_blobs)
    monkeypatch.setenv("FALLBACK_RECOVERY_BLOBS", fallback_recovery_blobs)
    monkeypatch.setenv("FALLBACK_LISTING_FAILURE_PREFIX", fallback_listing_failure_prefix)
    monkeypatch.setenv("SOFT_DELETED_BLOBS_JSON", soft_deleted_blobs_json)
    monkeypatch.setenv(
        "SOFT_DELETED_LISTING_FAILURE",
        str(soft_deleted_listing_failure).lower(),
    )
    monkeypatch.setenv(
        "REMOVE_CANONICAL_AFTER_UPLOAD",
        str(remove_canonical_after_upload).lower(),
    )
    monkeypatch.setenv("CLEANUP_FAILED_BLOB", cleanup_failed_blob)
    monkeypatch.setenv("HOSTED_TRACE_LOG", str(capture_path / "trace.log"))
    monkeypatch.setenv("RETENTION_FAILURE", str(retention_failure).lower())
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


def _telemetry_records(result: subprocess.CompletedProcess[str]) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in result.stdout.splitlines()
        if line.startswith("{")
    ]


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
    trace = (capture_path / "trace.log").read_text(encoding="utf-8").splitlines()
    assert trace.index(
        "saltbytes:retention --database data/local/saltbytes.duckdb --json"
    ) < trace.index("az:upload:raw/run/a.json")
    records = _telemetry_records(result)
    assert [record["record_type"] for record in records] == [
        "database_retention",
        "hosted_storage_lifecycle",
    ]
    assert records[0]["schema"] == "saltbytes.storage-lifecycle"
    assert records[0]["version"] == 1
    assert records[1]["canonical_duckdb"] == {
        "payload_bytes": (capture_path / "state__saltbytes.duckdb").stat().st_size,
        "status": "available",
    }
    assert records[1]["prefixes"] == {
        "raw/": {
            "active_before_cleanup": {"count": 0, "payload_bytes": 0},
            "active_after_cleanup": {"count": 0, "payload_bytes": 0},
            "cleanup_candidates": {"count": 0, "payload_bytes": 0},
            "failed_removals": {"count": 0, "payload_bytes": 0},
            "status": "available",
            "successful_removals": {"count": 0, "payload_bytes": 0},
        },
        "recovery/": {
            "active_before_cleanup": {"count": 0, "payload_bytes": 0},
            "active_after_cleanup": {"count": 0, "payload_bytes": 0},
            "cleanup_candidates": {"count": 0, "payload_bytes": 0},
            "failed_removals": {"count": 0, "payload_bytes": 0},
            "status": "available",
            "successful_removals": {"count": 0, "payload_bytes": 0},
        },
    }


def test_observation_source_failure_keeps_publication_and_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, _ = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        observation_failure_output=(
            "Sunset Beach Pier status: failed: report entries missing"
        ),
    )

    assert result.returncode == 0
    assert uploads[-1] == "state/saltbytes.duckdb"
    assert (
        "Sunset Beach Pier status: failed: report entries missing" in result.stderr
    )
    assert (
        "fishing observation ingestion had source failures; "
        "source outcomes are shown above"
    ) in result.stderr
    assert "preserved prior observation state" not in result.stderr


def test_retention_failure_prevents_raw_and_canonical_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        retention_failure=True,
    )

    assert result.returncode == 1
    assert uploads == []
    assert "environmental retention failed; canonical state unchanged" in result.stderr
    trace = (capture_path / "trace.log").read_text(encoding="utf-8")
    assert "saltbytes:retention --database data/local/saltbytes.duckdb --json" in trace
    assert "az:upload:" not in trace
    assert "az:list:" not in trace


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
    trace = (capture_path / "trace.log").read_text(encoding="utf-8")
    assert "az:list:raw/" not in trace
    assert "az:list:recovery/" not in trace


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


def test_successful_publication_cleans_only_expired_raw_and_recovery_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        raw_blobs_json=json.dumps(
            [
                {
                    "name": "raw/2026/expired.json",
                    "properties": {
                        "contentLength": 40,
                        "lastModified": "2020-01-01T00:00:00Z",
                    },
                },
                {
                    "name": "raw/2026/current.json",
                    "properties": {
                        "contentLength": 60,
                        "lastModified": "2099-01-01T00:00:00Z",
                    },
                },
            ]
        ),
        recovery_blobs_json=json.dumps(
            [
                {
                    "name": "recovery/expired/saltbytes.duckdb",
                    "properties": {
                        "contentLength": 80,
                        "lastModified": "2020-01-01T00:00:00Z",
                    },
                }
            ]
        ),
        soft_deleted_blobs_json=json.dumps(
            [
                {
                    "name": "state/saltbytes.duckdb",
                    "deleted": True,
                    "snapshot": "2026-09-12T00:00:00Z",
                    "properties": {"contentLength": 125},
                },
                {
                    "name": "state/saltbytes.duckdb.other",
                    "deleted": True,
                    "snapshot": "2026-09-12T00:00:00Z",
                    "properties": {"contentLength": 999},
                },
            ]
        ),
    )

    assert result.returncode == 0
    assert uploads[-1] == "state/saltbytes.duckdb"
    trace = (capture_path / "trace.log").read_text(encoding="utf-8").splitlines()
    state_upload_index = trace.index("az:upload:state/saltbytes.duckdb")
    cleanup_trace = trace[state_upload_index + 1 :]
    assert cleanup_trace[0] == "az:list:raw/:num-results=*:query=:include="
    assert cleanup_trace[1] == "az:delete:raw/2026/expired.json"
    assert cleanup_trace[2] == "az:list:recovery/:num-results=*:query=:include="
    assert cleanup_trace[3] == "az:delete:recovery/expired/saltbytes.duckdb"
    assert cleanup_trace[4] == (
        "az:list:state/saltbytes.duckdb:num-results=*:query=:include=ds"
    )
    assert not any(entry.startswith("az:delete:state/") for entry in trace)
    assert "historical artifact cleanup totals: total=2 removed=2 failed=0" in result.stdout
    storage_record = _telemetry_records(result)[1]
    assert storage_record["prefixes"]["raw/"] == {
        "active_before_cleanup": {"count": 2, "payload_bytes": 100},
        "active_after_cleanup": {"count": 1, "payload_bytes": 60},
        "cleanup_candidates": {"count": 1, "payload_bytes": 40},
        "failed_removals": {"count": 0, "payload_bytes": 0},
        "status": "available",
        "successful_removals": {"count": 1, "payload_bytes": 40},
    }
    assert storage_record["prefixes"]["recovery/"] == {
        "active_before_cleanup": {"count": 1, "payload_bytes": 80},
        "active_after_cleanup": {"count": 0, "payload_bytes": 0},
        "cleanup_candidates": {"count": 1, "payload_bytes": 80},
        "failed_removals": {"count": 0, "payload_bytes": 0},
        "status": "available",
        "successful_removals": {"count": 1, "payload_bytes": 80},
    }
    assert storage_record["canonical_soft_deleted_snapshots"] == {
        "count": 1,
        "payload_bytes": 125,
        "status": "available",
    }


def test_malformed_rich_inventory_falls_back_to_required_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        raw_blobs_json="not-json",
        fallback_raw_blobs="raw/2026/expired.json",
    )

    assert result.returncode == 0
    assert uploads[-1] == "state/saltbytes.duckdb"
    trace = (capture_path / "trace.log").read_text(encoding="utf-8").splitlines()
    raw_listings = [entry for entry in trace if entry.startswith("az:list:raw/")]
    assert len(raw_listings) == 2
    assert raw_listings[0] == "az:list:raw/:num-results=*:query=:include="
    assert raw_listings[1].startswith(
        "az:list:raw/:num-results=*:query=[?properties.lastModified < '"
    )
    assert "az:delete:raw/2026/expired.json" in trace
    assert "rich historical artifact telemetry unavailable: raw/" in result.stderr
    assert "historical artifact cleanup totals: total=1 removed=1 failed=0" in result.stdout
    assert _telemetry_records(result)[1]["prefixes"]["raw/"] == {
        "active_after_cleanup": None,
        "active_before_cleanup": None,
        "cleanup_candidates": None,
        "failed_removals": None,
        "status": "unavailable",
        "successful_removals": None,
    }


def test_required_fallback_listing_failure_is_fatal_and_stops_later_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        raw_blobs_json="not-json",
        fallback_listing_failure_prefix="raw/",
        recovery_blobs_json=json.dumps(
            [
                {
                    "name": "recovery/expired/saltbytes.duckdb",
                    "properties": {
                        "contentLength": 80,
                        "lastModified": "2020-01-01T00:00:00Z",
                    },
                }
            ]
        ),
    )

    assert result.returncode == 1
    assert uploads[-1] == "state/saltbytes.duckdb"
    trace = (capture_path / "trace.log").read_text(encoding="utf-8")
    assert "required historical artifact listing failed: raw/" in result.stderr
    assert "az:delete:" not in trace
    assert "az:list:recovery/" not in trace
    assert "recovery/run123/saltbytes.duckdb" not in uploads
    assert (
        "final hosted outcome: canonical state published; "
        "historical artifact cleanup failed"
    ) in result.stderr


def test_cleanup_failure_after_canonical_publication_fails_the_hosted_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, capture_path = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        raw_blobs_json=json.dumps(
            [
                {
                    "name": "raw/2026/expired.json",
                    "properties": {
                        "contentLength": 55,
                        "lastModified": "2020-01-01T00:00:00Z",
                    },
                }
            ]
        ),
        recovery_blobs_json=json.dumps(
            [
                {
                    "name": "recovery/expired/saltbytes.duckdb",
                    "properties": {
                        "contentLength": 80,
                        "lastModified": "2020-01-01T00:00:00Z",
                    },
                }
            ]
        ),
        cleanup_failed_blob="raw/2026/expired.json",
    )

    assert result.returncode == 1
    assert uploads[-1] == "state/saltbytes.duckdb"
    assert "recovery/run123/saltbytes.duckdb" not in uploads
    trace = (capture_path / "trace.log").read_text(encoding="utf-8")
    assert "az:upload:state/saltbytes.duckdb" in trace
    assert "az:delete:raw/2026/expired.json" in trace
    assert "az:list:recovery/" not in trace
    assert "az:delete:recovery/expired/saltbytes.duckdb" not in trace
    assert "historical artifact deletion failed: raw/2026/expired.json" in result.stderr
    assert "completed run database validation failed" not in result.stdout
    assert (
        "final hosted outcome: canonical state published; "
        "historical artifact cleanup failed"
    ) in result.stderr
    raw_metrics = _telemetry_records(result)[1]["prefixes"]["raw/"]
    assert raw_metrics["cleanup_candidates"] == {"count": 1, "payload_bytes": 55}
    assert raw_metrics["successful_removals"] == {"count": 0, "payload_bytes": 0}
    assert raw_metrics["failed_removals"] == {"count": 1, "payload_bytes": 55}
    assert raw_metrics["active_after_cleanup"] == {"count": 1, "payload_bytes": 55}


def test_soft_deleted_snapshot_listing_failure_is_visible_and_nonfatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, _ = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        soft_deleted_listing_failure=True,
    )

    assert result.returncode == 0
    assert uploads[-1] == "state/saltbytes.duckdb"
    assert "canonical soft-deleted snapshot telemetry unavailable: listing failed" in result.stderr
    storage_record = _telemetry_records(result)[1]
    assert storage_record["canonical_soft_deleted_snapshots"] == {
        "count": None,
        "payload_bytes": None,
        "status": "unavailable",
    }


def test_canonical_size_observation_failure_is_visible_and_nonfatal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, uploads, _ = _run_hosted_ingestion(
        tmp_path,
        monkeypatch,
        remove_canonical_after_upload=True,
    )

    assert result.returncode == 0
    assert uploads[-1] == "state/saltbytes.duckdb"
    assert (
        "canonical database payload telemetry unavailable: size observation failed"
        in result.stderr
    )
    storage_record = _telemetry_records(result)[1]
    assert storage_record["canonical_duckdb"] == {
        "payload_bytes": None,
        "status": "unavailable",
    }
