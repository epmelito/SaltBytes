import hashlib
import re
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import duckdb
import httpx

from saltbytes.database import initialize_database

JENNETTES_PIER_URL = "https://www.ncaquariums.com/jennettes-pier"
_NAMED_CATCH = re.compile(r"^(?P<name>[A-Z][A-Za-z .'-]+) caught (?:a |an )?(?P<subject>.+)$")
_CAUGHT_SUMMARY = re.compile(r"(?:anglers have )?caught\s+(?P<subject>.+)$", re.I)
_BEING_CAUGHT = re.compile(r"^(?P<subject>.+?)\s+(?:are|is) being caught\b", re.I)
_BITING = re.compile(r"\b(?P<subject>[A-Z][A-Z ]*[A-Z])\s+biting\b")


class ObservationParseError(ValueError):
    """The public report surface no longer has the bounded recognizable shape."""


class _ReportCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_card = False
        self.in_info = False
        self.capture: str | None = None
        self.text: list[str] = []
        self.current: dict[str, object] | None = None
        self.reports: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "li" and "card" in attributes.get("class", "").split():
            self.in_card = True
            self.current = {"report_time_text": None, "report_title": None, "body": []}
            return
        if not self.in_card:
            return
        if tag == "div" and "report-info" in attributes.get("class", "").split():
            self.in_info = True
        if (
            self.in_info
            and tag == "span"
            and "report-info__date" in attributes.get("class", "").split()
        ):
            self.capture, self.text = "date", []
        elif self.in_info and tag == "h3":
            self.capture, self.text = "title", []
        elif self.in_info and tag == "p":
            self.capture, self.text = "body", []

    def handle_data(self, data: str) -> None:
        if self.capture is not None:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_card:
            return
        if self.capture == "date" and tag == "span":
            self.current["report_time_text"] = " ".join("".join(self.text).split())
            self.capture = None
        elif self.capture == "title" and tag == "h3":
            self.current["report_title"] = " ".join("".join(self.text).split())
            self.capture = None
        elif self.capture == "body" and tag == "p":
            text = " ".join("".join(self.text).split())
            if text:
                self.current["body"].append(text)
            self.capture = None
        if tag == "div" and self.in_info:
            self.in_info = False
        if tag == "li" and self.current is not None:
            self.reports.append(self.current)
            self.current = None
            self.in_card = False


def fetch_jennettes_pier_report(timeout_seconds: float = 10.0) -> str:
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.get(JENNETTES_PIER_URL)
    response.raise_for_status()
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ObservationParseError("Jennette's Pier response is not HTML")
    return response.text


def extract_jennettes_pier_reports(html: str) -> tuple[list[dict[str, str]], dict[str, int]]:
    if not isinstance(html, str) or not html.strip():
        raise ObservationParseError("Jennette's Pier report HTML is empty")
    parser = _ReportCardParser()
    parser.feed(html)
    if any(not report["body"] for report in parser.reports):
        raise ObservationParseError(
            "Jennette's Pier report card is missing a recognized body paragraph"
        )
    reports = [
        {
            "report_time_text": report["report_time_text"] or "",
            "report_title": report["report_title"] or "",
            "body": " ".join(report["body"]),
        }
        for report in parser.reports
        if report["body"]
    ]
    if not reports:
        raise ObservationParseError("Jennette's Pier report cards were not recognized")
    if any(not report["report_time_text"] for report in reports):
        raise ObservationParseError("Jennette's Pier report card is missing report-info__date")
    return reports, {"report_envelopes": len(parser.reports), "body_envelopes": len(reports)}


def _time_text(sentence: str) -> str | None:
    lower = sentence.lower()
    if match := re.search(r"\b(yesterday|today)\s+(mid-morning|morning)\b", lower):
        return match[0]
    if "mid-morning" in lower:
        return "mid-morning"
    if "this morning" in lower:
        return "this morning"
    if "morning" in lower:
        return "morning"
    return "yesterday" if "yesterday" in lower else "today" if "today" in lower else None


def _subject(text: str) -> str | None:
    value = re.sub(
        r"\b(?:yesterday|today)\s+(?:mid-morning|morning)\b|\bthis morning|\bmid-morning|"
        r"\bmorning\b|\b(?:today|yesterday)\b",
        "",
        text,
        flags=re.I,
    ).strip(" .,!;:")
    return value or None


def _summary_subject(sentence: str) -> str | None:
    values = re.findall(r"\b[A-Z]{2,}\b", sentence)
    lower = sentence.lower()
    has_catch_list_structure = sentence.count(",") >= 2 or (
        "small " in lower and re.search(r"&|\band\b", lower) is not None
    ) or re.search(r"\b(?:mid-)?morning update:", lower) is not None
    if len(values) >= 2 and has_catch_list_structure:
        return sentence.strip(" .")
    return None


def _candidate_reason(sentence: str) -> str | None:
    lower = sentence.lower()
    if any(word in lower for word in ("fish", "catch", "angler", "bait", "pier")):
        return "fishing terminology"
    if any(word in lower for word in ("wind", "ocean", "water", "tide", "sea")):
        return "environmental terminology"
    if re.search(r"\b[A-Z]{2,}\b", sentence) and any(character.isdigit() for character in sentence):
        return "source notation"
    return None


def _assertion(
    kind: str, granularity: str, basis: str, time: str | None, subject: str | None, text: str
) -> dict[str, str | None]:
    return {
        "assertion_kind": kind,
        "granularity": granularity,
        "evidence_basis": basis,
        "observation_time_text": time,
        "raw_subject": subject,
        "assertion_text": text,
    }


def _assertions_for_report(
    report: dict[str, str],
) -> tuple[list[dict[str, str | None]], list[dict[str, str]], dict[str, int]]:
    assertions: list[dict[str, str | None]] = []
    segments = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", report["body"])
        if sentence.strip()
    ]
    candidates: list[dict[str, str]] = []
    classified_segments = 0
    for sentence in segments:
        lower, time = sentence.lower(), _time_text(sentence)
        produced = 0
        if "slow" in lower or "quiet day" in lower:
            assertions.append(
                _assertion(
                    "interpretation", "site_summary", "source_staff_summary", time, None, sentence
                )
            )
            produced += 1
        factual_environment = not any(
            word in lower for word in ("should", "expect", "recommend", "will be")
        ) and (
            re.search(
                r"\b(winds?\b.*\b[nesw]{1,3}\b|[nesw]{1,3}\s+winds?|wind\s+[nesw]{1,3}|"
                r"ocean temp|water temp|water is \d|sea is flat|flat, glassy ocean)",
                lower,
            )
            is not None
        )
        if factual_environment:
            assertions.append(
                _assertion(
                    "environmental_context",
                    "site_summary",
                    "source_staff_summary",
                    time,
                    "reported environmental context",
                    sentence,
                )
            )
            produced += 1
        negated = re.search(
            r"\b(no|none|nothing|nobody)\b.*\b(catch|caught|catching)\b|"
            r"\b(catch|caught|catching)\s+(?:no|none|nothing|zero|0)\b",
            lower,
        )
        if re.search(r"\bno one is fishing\b", lower):
            assertions.append(
                _assertion(
                    "fishing_activity", "site_summary", "source_staff_summary", time, None, sentence
                )
            )
            produced += 1
        elif not negated:
            named = _NAMED_CATCH.match(sentence)
            being_caught = _BEING_CAUGHT.match(sentence)
            caught = _CAUGHT_SUMMARY.search(sentence)
            biting = _BITING.search(sentence)
            subject = None
            if named and not named["name"].lower().startswith("anglers"):
                assertions.append(
                    _assertion(
                        "catch",
                        "individual_event",
                        "named_angler_customer_report",
                        time,
                        _subject(named["subject"]),
                        sentence,
                    )
                )
                produced += 1
            elif being_caught:
                assertions.append(
                    _assertion(
                        "catch",
                        "site_summary",
                        "source_staff_summary",
                        time,
                        _subject(being_caught["subject"]),
                        sentence,
                    )
                )
                produced += 1
            elif caught:
                assertions.append(
                    _assertion(
                        "catch",
                        "site_summary",
                        "source_staff_summary",
                        time,
                        _subject(caught["subject"]),
                        sentence,
                    )
                )
                produced += 1
            elif biting:
                assertions.append(
                    _assertion(
                        "presence_sighting",
                        "site_summary",
                        "source_staff_summary",
                        time,
                        biting["subject"],
                        sentence,
                    )
                )
                produced += 1
            elif not factual_environment and (subject := _summary_subject(sentence)) is not None:
                assertions.append(
                    _assertion(
                        "catch", "site_summary", "source_staff_summary", time, subject, sentence
                    )
                )
                produced += 1
        if produced:
            classified_segments += 1
        elif (reason := _candidate_reason(sentence)) is not None:
            candidates.append({"raw_segment": sentence, "reason": reason})
    return (
        assertions,
        candidates,
        {
            "segments_considered": len(segments),
            "classified_segments": classified_segments,
            "review_candidate_segments": len(candidates),
            "other_unclassified_segments": len(segments) - classified_segments - len(candidates),
        },
    )


def _persist_candidate(
    connection: duckdb.DuckDBPyConnection,
    candidate_id: str,
    report_id: str,
    raw_segment: str,
    reason: str,
) -> bool:
    is_new = (
        connection.execute(
            """select count(*) from fishing_observation_review_candidates
            where candidate_id = ?""",
            [candidate_id],
        ).fetchone()[0]
        == 0
    )
    connection.execute(
        """insert into fishing_observation_review_candidates values (?, ?, ?, ?)
        on conflict do nothing""",
        [candidate_id, report_id, raw_segment, reason],
    )
    return is_new


def ingest_jennettes_pier(
    database_path: Path | str, html: str, retrieved_at: datetime | None = None
) -> dict[str, object]:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must include timezone information")
    reports, diagnostics = extract_jennettes_pier_reports(html)
    initialize_database(database_path)
    inserted_reports = inserted_assertions = inserted_candidates = zero_assertion_reports = 0
    kinds: Counter[str] = Counter()
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("begin transaction")
        try:
            for report in reports:
                content_hash = hashlib.sha256(
                    (
                        report["report_time_text"]
                        + "\n"
                        + report["report_title"]
                        + "\n"
                        + report["body"]
                    ).encode()
                ).hexdigest()
                report_id = hashlib.sha256(
                    f"jennettes_pier|{JENNETTES_PIER_URL}|{content_hash}".encode()
                ).hexdigest()
                assertions, candidates, segment_diagnostics = _assertions_for_report(report)
                diagnostics["segments_considered"] = (
                    diagnostics.get("segments_considered", 0)
                    + segment_diagnostics["segments_considered"]
                )
                for key in (
                    "classified_segments",
                    "review_candidate_segments",
                    "other_unclassified_segments",
                ):
                    diagnostics[key] = diagnostics.get(key, 0) + segment_diagnostics[key]
                zero_assertion_reports += int(not assertions)
                inserted_reports += int(
                    connection.execute(
                        "select count(*) from fishing_observation_reports where report_id = ?",
                        [report_id],
                    ).fetchone()[0]
                    == 0
                )
                connection.execute(
                    """insert into fishing_observation_reports values
                    (?, 'jennettes_pier', ?, ?, ?, ?, 'jennettes_pier', 'exact_site', ?)
                    on conflict do nothing""",
                    [
                        report_id,
                        JENNETTES_PIER_URL,
                        content_hash,
                        report["report_time_text"] or None,
                        report["report_title"] or None,
                        retrieved_at,
                    ],
                )
                connection.execute(
                    """insert into fishing_observation_retrievals values (?, ?)
                    on conflict do nothing""",
                    [report_id, retrieved_at],
                )
                for assertion in assertions:
                    kinds[assertion["assertion_kind"]] += 1
                    assertion_id = hashlib.sha256(
                        f"{report_id}|{assertion['assertion_kind']}|{assertion['granularity']}|{assertion['evidence_basis']}|{assertion['observation_time_text']}|{assertion['raw_subject']}|{assertion['assertion_text']}".encode()
                    ).hexdigest()
                    inserted_assertions += int(
                        connection.execute(
                            """select count(*) from fishing_observation_assertions
                            where assertion_id = ?""",
                            [assertion_id],
                        ).fetchone()[0]
                        == 0
                    )
                    connection.execute(
                        """insert into fishing_observation_assertions values
                        (?, ?, ?, ?, ?, ?, ?, ?) on conflict do nothing""",
                        [
                            assertion_id,
                            report_id,
                            assertion["assertion_kind"],
                            assertion["granularity"],
                            assertion["evidence_basis"],
                            assertion["observation_time_text"],
                            assertion["raw_subject"],
                            assertion["assertion_text"],
                        ],
                    )
                for candidate in candidates:
                    candidate_id = hashlib.sha256(
                        f"{report_id}|{candidate['reason']}|{candidate['raw_segment']}".encode()
                    ).hexdigest()
                    inserted_candidates += int(
                        _persist_candidate(
                            connection,
                            candidate_id,
                            report_id,
                            candidate["raw_segment"],
                            candidate["reason"],
                        )
                    )
            connection.execute("commit")
        except Exception:
            connection.execute("rollback")
            raise
    return {
        "reports": inserted_reports,
        "assertions": inserted_assertions,
        "review_candidates": inserted_candidates,
        "retrievals": len(reports),
        **diagnostics,
        "assertions_by_kind": dict(kinds),
        "zero_assertion_reports": zero_assertion_reports,
    }


def retrieve_and_ingest_jennettes_pier(database_path: Path | str) -> dict[str, object]:
    return ingest_jennettes_pier(database_path, fetch_jennettes_pier_report())
