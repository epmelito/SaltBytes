# ruff: noqa: E501

from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from saltbytes.observations import (
    ObservationParseError,
    ingest_jennettes_pier,
    retrieve_and_record_jennettes_pier_attempt,
    review_jennettes_pier_candidates,
)


def _card(date: str, title: str, body: str) -> str:
    return f'<li class="card"><div class="report"><div class="report-info"><span class="report-info__date">{date}</span><h3>{title}</h3><p>{body}</p></div></div></li>'


def _html(*cards: str) -> str:
    return f"<html><body><ul>{''.join(cards)}</ul></body></html>"


def test_structural_cards_preserve_real_world_language_families(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    html = _html(
        _card(
            "WEDNESDAY, AUG. 12",
            "CALM SEAS",
            "Great variety so far, BAR JACK, BLUEFISH, CROAKER, small FLOUNDER, PINFISH and PIGFISH. Winds are West at 7 knots. The sea is flat and water is 72 degrees.",
        ),
        _card(
            "TUESDAY, AUGUST 11",
            "QUIET DAY",
            "Small CROAKER and SPOT. Sunny and hot, wind WSW 5-10 mph. Flat, glassy ocean, water temp 67. A photo update.",
        ),
        _card(
            "SATURDAY AUG. 8, 2026",
            "NICE MORNING",
            "SAND PERCH, BLUEFISH, CROAKER & SPOT are being caught today.",
        ),
        _card(
            "FRIDAY, AUG. 7",
            "BLUE SKIES",
            "So far, anglers have caught 3# SHEEPSHEAD, BLUEFISH, SEA MULLET. Same winds as yesterday, SW at 10 knots.",
        ),
        _card(
            "THURSDAY, AUG. 6",
            "BLUES",
            "Mid-morning update: BLUEFISH, BLACK SEA BASS, CROAKER, SPOT, FLOUNDER AND SAND PERCH. Another morning of BLUEFISH biting!",
        ),
    )
    result = ingest_jennettes_pier(database_path, html, datetime.now(timezone.utc))
    with duckdb.connect(str(database_path), read_only=True) as connection:
        assertions = connection.execute(
            "select assertion_kind, observation_time_text, raw_subject from fishing_observation_assertions"
        ).fetchall()

    assert result["report_envelopes"] == result["body_envelopes"] == 5
    assert result["other_unclassified_segments"] == 1
    assert (
        "catch",
        None,
        "Great variety so far, BAR JACK, BLUEFISH, CROAKER, small FLOUNDER, PINFISH and PIGFISH",
    ) in assertions
    assert ("catch", "today", "SAND PERCH, BLUEFISH, CROAKER & SPOT") in assertions
    assert ("catch", None, "3# SHEEPSHEAD, BLUEFISH, SEA MULLET") in assertions
    assert ("presence_sighting", "morning", "BLUEFISH") in assertions
    assert ("environmental_context", "yesterday", "reported environmental context") in assertions


def test_versions_are_content_identity_and_unchanged_retrieval_is_idempotent(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "observations.duckdb"
    first = _html(_card("TUESDAY, JULY 28", "EDITORIAL TITLE", "George caught a TARPON yesterday."))
    changed = _html(
        _card("TUESDAY, JULY 28", "CORRECTED TITLE", "George caught a COBIA yesterday.")
    )
    ingest_jennettes_pier(database_path, first, datetime(2026, 8, 12, 12, tzinfo=timezone.utc))
    update = ingest_jennettes_pier(
        database_path, changed, datetime(2026, 8, 12, 13, tzinfo=timezone.utc)
    )
    repeat = ingest_jennettes_pier(
        database_path, changed, datetime(2026, 8, 12, 14, tzinfo=timezone.utc)
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        counts = connection.execute(
            "select (select count(*) from fishing_observation_reports), (select count(*) from fishing_observation_retrievals), (select count(*) from fishing_observation_assertions)"
        ).fetchone()
        subjects = connection.execute(
            "select raw_subject from fishing_observation_assertions order by raw_subject"
        ).fetchall()

    assert update["reports"] == update["assertions"] == 1
    assert repeat["reports"] == repeat["assertions"] == 0
    assert counts == (2, 3, 2)
    assert subjects == [("COBIA",), ("TARPON",)]


def test_activity_and_negation_remain_nonabsence(tmp_path: Path) -> None:
    html = _html(
        _card(
            "broken date",
            "QUIET",
            "No One Is Fishing Today. No BLUEFISH caught today. George caught no BLUEFISH today. George caught a TARPON yesterday. Fishin' kinda slow.",
        )
    )
    database_path = tmp_path / "observations.duckdb"
    result = ingest_jennettes_pier(database_path, html, datetime.now(timezone.utc))
    with duckdb.connect(str(database_path), read_only=True) as connection:
        assertions = connection.execute(
            "select assertion_kind, observation_time_text, raw_subject from fishing_observation_assertions"
        ).fetchall()

    assert result["reports"] == 1
    assert ("fishing_activity", "today", None) in assertions
    assert ("catch", "yesterday", "TARPON") in assertions
    assert ("interpretation", None, None) in assertions
    assert all(subject != "BLUEFISH" for _, _, subject in assertions)


@pytest.mark.parametrize(
    ("sentence", "expected_time", "expected_subject"),
    [
        ("George caught a TARPON yesterday morning.", "yesterday morning", "TARPON"),
        ("George caught a TARPON today morning.", "today morning", "TARPON"),
        ("George caught a TARPON this morning.", "this morning", "TARPON"),
        ("George caught a TARPON mid-morning.", "mid-morning", "TARPON"),
        ("George caught a TARPON morning.", "morning", "TARPON"),
    ],
)
def test_source_supported_daypart_and_relative_day_are_preserved(
    tmp_path: Path,
    sentence: str,
    expected_time: str,
    expected_subject: str,
) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", sentence)),
        datetime.now(timezone.utc),
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            "select observation_time_text, raw_subject from fishing_observation_assertions"
        ).fetchone()
    assert row == (expected_time, expected_subject)


def test_explicit_negative_catch_and_uppercase_prose_do_not_become_catches(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(
            _card(
                "DATE",
                "REPORT",
                "Nobody caught BLUEFISH today. No BLUEFISH caught today. George caught no BLUEFISH today. George caught nothing today. George caught none today. George caught zero BLUEFISH today. George caught 0 BLUEFISH today. Anglers caught nothing today. HIGH TIDE 8:42 AM. PARKING LOT CLOSED TODAY. BLUE SKIES, HIGH TIDE 8:42 AM. HIGH TIDE & PARKING LOT CLOSED TODAY.",
            )
        ),
        datetime.now(timezone.utc),
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        assertions = connection.execute(
            "select assertion_kind, assertion_text from fishing_observation_assertions"
        ).fetchall()
    assert all(kind != "catch" for kind, _ in assertions)
    assert sum(kind == "environmental_context" for kind, _ in assertions) == 3


@pytest.mark.parametrize(
    "sentence",
    ["Anglers caught BLUEFISH today.", "Anglers have caught BLUEFISH today."],
)
def test_anglers_caught_is_a_site_summary_not_an_individual_event(
    tmp_path: Path,
    sentence: str,
) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", sentence)),
        datetime.now(timezone.utc),
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            "select granularity, evidence_basis, raw_subject from fishing_observation_assertions"
        ).fetchone()
    assert row == ("site_summary", "source_staff_summary", "BLUEFISH")


def test_named_angler_catch_remains_an_individual_event(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", "George caught a TARPON today.")),
        datetime.now(timezone.utc),
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            "select granularity, evidence_basis, raw_subject from fishing_observation_assertions"
        ).fetchone()
    assert row == ("individual_event", "named_angler_customer_report", "TARPON")


def test_environmental_and_catch_families_do_not_cross_contaminate(tmp_path: Path) -> None:
    html = _html(
        _card(
            "DATE",
            "REPORT",
            "George caught a TARPON in the water today. Winds SW to WSW at 10 knots. Mid-morning update: BLUEFISH, BLACK SEA BASS.",
        )
    )
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(database_path, html, datetime.now(timezone.utc))
    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(
            "select assertion_kind, observation_time_text, raw_subject from fishing_observation_assertions"
        ).fetchall()
    assert ("catch", "today", "TARPON in the water") in rows
    assert ("environmental_context", None, "reported environmental context") in rows
    assert ("catch", "mid-morning", "Mid-morning update: BLUEFISH, BLACK SEA BASS") in rows
    assert sum(kind == "catch" for kind, _, _ in rows) == 2


def test_structurally_missing_cards_fail(tmp_path: Path) -> None:
    with pytest.raises(ObservationParseError, match="cards were not recognized"):
        ingest_jennettes_pier(tmp_path / "observations.duckdb", "<p>not a report</p>")


def test_missing_structural_date_fails_but_raw_malformed_date_is_preserved(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    malformed = _html(_card("SATURAY, AUG. 15", "REPORT", "BLUEFISH biting."))
    ingest_jennettes_pier(database_path, malformed, datetime.now(timezone.utc))
    with duckdb.connect(str(database_path), read_only=True) as connection:
        assert connection.execute(
            "select report_time_text from fishing_observation_reports"
        ).fetchone() == ("SATURAY, AUG. 15",)
    missing = '<li class="card"><div class="report"><div class="report-info"><h3>REPORT</h3><p>BLUEFISH biting.</p></div></div></li>'
    with pytest.raises(ObservationParseError, match="missing report-info__date"):
        ingest_jennettes_pier(
            tmp_path / "missing.duckdb", _html(missing), datetime.now(timezone.utc)
        )


def test_partial_report_card_body_drift_fails_explicitly(tmp_path: Path) -> None:
    incomplete = '<li class="card"><div class="report"><div class="report-info"><span class="report-info__date">DATE</span><h3>REPORT</h3></div></div></li>'
    with pytest.raises(ObservationParseError, match="missing a recognized body paragraph"):
        ingest_jennettes_pier(
            tmp_path / "observations.duckdb",
            _html(_card("DATE", "REPORT", "BLUEFISH biting."), incomplete),
            datetime.now(timezone.utc),
        )


def test_candidates_are_version_linked_not_assertions_or_other_prose(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    html = _html(_card("DATE", "REPORT", "Anglers were nearby. Community photo event."))
    first = ingest_jennettes_pier(database_path, html, datetime.now(timezone.utc))
    second = ingest_jennettes_pier(database_path, html, datetime.now(timezone.utc))
    with duckdb.connect(str(database_path), read_only=True) as connection:
        candidates = connection.execute(
            """
            select candidate.report_id, candidate.raw_segment, candidate.reason
            from fishing_observation_review_candidates candidate
            join fishing_observation_reports report using (report_id)
            """
        ).fetchall()
        assertions = connection.execute(
            "select count(*) from fishing_observation_assertions"
        ).fetchone()
    assert first["review_candidates"] == 1
    assert second["review_candidates"] == 0
    assert len(candidates) == 1
    assert candidates[0][0]
    assert candidates[0][1:] == ("Anglers were nearby.", "fishing terminology")
    assert assertions == (0,)


def test_candidate_patterns_group_versions_and_retain_review_disposition(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    first = ingest_jennettes_pier(
        database_path,
        _html(
            _card("DATE", "REPORT", "Anglers were nearby."),
            _card("DATE", "UPDATED REPORT", "Anglers were nearby. Community photo event."),
        ),
        datetime.now(timezone.utc),
    )

    review = review_jennettes_pier_candidates(database_path)
    pattern = review["patterns"][0]
    reviewed = review_jennettes_pier_candidates(
        database_path,
        pattern_id=pattern["pattern_id"],
        disposition="irrelevant",
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        disposition = connection.execute(
            """select disposition from fishing_observation_review_patterns
            where pattern_id = ?""",
            [pattern["pattern_id"]],
        ).fetchone()

    assert first["new_review_patterns"] == 1
    assert first["previously_seen_review_patterns"] == 0
    assert review["outstanding_patterns"] == 1
    assert pattern["occurrence_count"] == len(pattern["occurrences"]) == 2
    assert reviewed["outstanding_patterns"] == 0
    assert disposition == ("irrelevant",)

    later = ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "LATER REPORT", "Anglers were nearby.")),
        datetime.now(timezone.utc),
    )
    assert later["new_review_patterns"] == 0
    assert later["previously_seen_review_patterns"] == 1


@pytest.mark.parametrize(
    "disposition",
    ["irrelevant", "useful_existing_semantics", "accepted_for_parser"],
)
def test_review_accepts_only_approved_dispositions(tmp_path: Path, disposition: str) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", "Anglers were nearby.")),
        datetime.now(timezone.utc),
    )
    pattern_id = review_jennettes_pier_candidates(database_path)["patterns"][0]["pattern_id"]

    review_jennettes_pier_candidates(database_path, pattern_id=pattern_id, disposition=disposition)


@pytest.mark.parametrize("disposition", ["", "not useful", "useful", "accepted"])
def test_review_rejects_unknown_dispositions(tmp_path: Path, disposition: str) -> None:
    with pytest.raises(ValueError, match="disposition must be one of"):
        review_jennettes_pier_candidates(
            tmp_path / "observations.duckdb",
            pattern_id="pattern123",
            disposition=disposition,
        )


def test_database_initialization_backfills_existing_candidate_patterns(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", "Anglers were nearby.")),
        datetime.now(timezone.utc),
    )
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("delete from fishing_observation_review_candidate_patterns")
        connection.execute("delete from fishing_observation_review_patterns")

    review = review_jennettes_pier_candidates(database_path)

    assert review["outstanding_patterns"] == 1
    assert review["patterns"][0]["occurrence_count"] == 1


def test_observation_attempt_commits_with_successful_ingestion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "observations.duckdb"
    monkeypatch.setattr(
        "saltbytes.observations.fetch_jennettes_pier_report",
        lambda: _html(_card("DATE", "REPORT", "Anglers were nearby.")),
    )

    result = retrieve_and_record_jennettes_pier_attempt(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        counts = connection.execute(
            """select (select count(*) from fishing_observation_review_candidates),
            (select count(*) from fishing_observation_ingestion_attempts)"""
        ).fetchone()
        attempt = connection.execute(
            """select status, new_review_patterns, previously_seen_review_patterns,
            outstanding_review_patterns from fishing_observation_ingestion_attempts"""
        ).fetchone()
    assert result["new_review_patterns"] == 1
    assert counts == (1, 1)
    assert attempt == ("success", 1, 0, 1)


def test_success_attempt_failure_rolls_back_observation_changes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "observations.duckdb"
    attempted_at = datetime(2026, 8, 13, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "saltbytes.observations._persist_ingestion_attempt",
        lambda *_: (_ for _ in ()).throw(RuntimeError("attempt write failed")),
    )

    with pytest.raises(RuntimeError, match="attempt write failed"):
        ingest_jennettes_pier(
            database_path,
            _html(_card("DATE", "REPORT", "Anglers were nearby.")),
            attempted_at=attempted_at,
        )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        counts = connection.execute(
            """select (select count(*) from fishing_observation_reports),
            (select count(*) from fishing_observation_assertions),
            (select count(*) from fishing_observation_ingestion_attempts)"""
        ).fetchone()
    assert counts == (0, 0, 0)


def test_failed_observation_attempt_preserves_history_and_records_current_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", "Anglers were nearby.")),
    )
    monkeypatch.setattr(
        "saltbytes.observations.fetch_jennettes_pier_report",
        lambda: (_ for _ in ()).throw(ObservationParseError("source failed")),
    )

    with pytest.raises(ObservationParseError, match="source failed"):
        retrieve_and_record_jennettes_pier_attempt(database_path)

    with duckdb.connect(str(database_path), read_only=True) as connection:
        report_count = connection.execute(
            "select count(*) from fishing_observation_reports"
        ).fetchone()
        attempt = connection.execute(
            """select status, new_review_patterns, previously_seen_review_patterns,
            outstanding_review_patterns from fishing_observation_ingestion_attempts"""
        ).fetchone()
    assert report_count == (1,)
    assert attempt == ("failed", 0, 0, 1)


def test_observation_attempt_history_orders_latest_deterministically(tmp_path: Path) -> None:
    database_path = tmp_path / "observations.duckdb"
    for index, wording in enumerate(("Anglers were nearby.", "Bait was available.")):
        ingest_jennettes_pier(
            database_path,
            _html(_card("DATE", str(index), wording)),
            attempted_at=datetime(2026, 8, 13, 12, tzinfo=timezone.utc),
        )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        attempts = connection.execute(
            """select status from fishing_observation_ingestion_attempts
            order by attempted_at desc, attempt_id desc"""
        ).fetchall()
    assert attempts == [("success",), ("success",)]


@pytest.mark.parametrize(
    "sentence",
    [
        "High tide 12:51 p.m.",
        "High tides 5:39 a.m.",
        "Low tide 11:42 a.m.",
        "Low tides 6:33 a.m.",
        "Winds are West at 7 knots.",
        "There's a gentle SW breeze at 10 knots.",
        "Ocean cold again at 68 degrees.",
    ],
)
def test_approved_environmental_wording_is_preserved_raw(
    tmp_path: Path,
    sentence: str,
) -> None:
    database_path = tmp_path / "observations.duckdb"
    ingest_jennettes_pier(
        database_path,
        _html(_card("DATE", "REPORT", sentence)),
        datetime.now(timezone.utc),
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        row = connection.execute(
            """select assertion_kind, raw_subject, assertion_text
            from fishing_observation_assertions"""
        ).fetchone()
    assert row == ("environmental_context", "reported environmental context", sentence)


def test_pier_mention_alone_does_not_create_a_review_candidate(tmp_path: Path) -> None:
    result = ingest_jennettes_pier(
        tmp_path / "observations.duckdb",
        _html(_card("DATE", "REPORT", "The pier hosts a camp today.")),
        datetime.now(timezone.utc),
    )
    assert result["review_candidates"] == 0


def test_candidate_write_failure_rolls_back_observation_transaction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "observations.duckdb"
    monkeypatch.setattr(
        "saltbytes.observations._persist_candidate",
        lambda *_: (_ for _ in ()).throw(RuntimeError("candidate write failed")),
    )

    with pytest.raises(RuntimeError, match="candidate write failed"):
        ingest_jennettes_pier(
            database_path,
            _html(_card("DATE", "REPORT", "George caught a TARPON. Anglers were nearby.")),
            datetime.now(timezone.utc),
        )

    with duckdb.connect(str(database_path), read_only=True) as connection:
        counts = connection.execute(
            """
            select
                (select count(*) from fishing_observation_reports),
                (select count(*) from fishing_observation_retrievals),
                (select count(*) from fishing_observation_assertions),
                (select count(*) from fishing_observation_review_candidates)
            """
        ).fetchone()
    assert counts == (0, 0, 0, 0)
