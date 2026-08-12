# ruff: noqa: E501

from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from saltbytes.observations import ObservationParseError, ingest_jennettes_pier


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
    assert assertions == []


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
