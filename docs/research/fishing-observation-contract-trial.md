# Fishing observation contract trial

## Status

Completed bounded research. This document records evidence for a later fishing
observation requirements contract; it does not approve that contract, a schema,
collection method, or production source suitability.

## Research question

Can a source-independent `report -> assertions` model preserve varied public
fishing reports without inventing temporal or geographic precision, species
identity, abundance, environmental relationships, or fish absence?

## Sample and source references

The manual trial deliberately used difficult reports from these source classes.
This is a frozen research sample, not a live source registry or production
ranking.

| Source class and reference | Material cases preserved in the trial |
| --- | --- |
| Sunset Beach Pier daily reports | Report-day wind, tide, and water temperature with `YESTERDAY'S CATCH` |
| Jennette's Pier reports | Same-day catches, an individual catch from yesterday, and `No One Is Fishing Today` |
| Bogue Inlet Pier reports and Catch Boards | Report-day water temperature with earlier catches; exact dated and weighed catches, including estimated or released catches |
| Tradewinds / Ocracoke reporting | Ramp 72 and Ramp 70 surf reports, relative catch dates, sound or charter catches, and `39 Sea Mullet` over three hours |
| Little Bridge / Fishing Unlimited reporting | `past couple of days`, `still producing`, and `slow this morning` |
| North Carolina Division of Marine Fisheries recreational reports | Regional and fishing-mode summaries based on agency observation and angler interviews, with catches, advice, and seasonal interpretation mixed together |
| Ocean Isle Beach Pier reports | Exact catches, morning or evening differences, qualitative quantities, ambiguous `drum`, baitfish sightings, slow-fishing commentary, and tide advice |

The trial evaluated report text as published. It did not repeat the broader
observational-source investigation, collect content automatically, or determine
final source risk classifications.

## Frozen representative-report references

The completed trial evidence retains the following source-specific report-text
anchors. It does not retain stable report URLs, report titles, or publication
dates for these individual examples. That is an explicit evidence-retention gap:
this research does not reconstruct references or repeat source discovery.

| Source | Frozen report-text anchor | Exact report reference retained |
| --- | --- | --- |
| Sunset Beach Pier daily reports | Report-day wind, tide, and water temperature with `YESTERDAY'S CATCH` | No stable URL, title, or date in the completed trial evidence |
| Jennette's Pier reports | Same-day catches, a catch from yesterday, and `No One Is Fishing Today` | No stable URL, title, or date in the completed trial evidence |
| Bogue Inlet Pier reports and Catch Boards | Report-day water temperature with earlier catches; dated and weighed Catch Board catches | No stable URL, title, or date in the completed trial evidence |
| Tradewinds / Ocracoke reporting | Ramp 72 and Ramp 70 reports and `39 Sea Mullet` over three hours | No stable URL, title, or date in the completed trial evidence |
| Little Bridge / Fishing Unlimited reporting | `past couple of days`, `still producing`, and `slow this morning` | No stable URL, title, or date in the completed trial evidence |
| North Carolina Division of Marine Fisheries recreational reports | Regional and fishing-mode summaries mixing catches, advice, and seasonal interpretation | No stable URL, title, or date in the completed trial evidence |
| Ocean Isle Beach Pier reports | Catches, time-of-day differences, `drum`, baitfish sightings, slow-fishing commentary, and tide advice | No stable URL, title, or date in the completed trial evidence |

## Findings

### Time is not one field

A report can contain a page or publication time, a report-effective date stated
in content, and separate observation times or windows for individual assertions.
These values must remain distinct. Retrieval time cannot silently stand in for
publication or observation time.

Temporal precision must not exceed the source. The sample included exact dates,
relative dates such as yesterday or Saturday, dayparts, approximate periods such
as past couple of days or all week, and reports without a reliable publication
or effective time.

### Assertions require classification

The trial supports factual catch observations, fish or bait presence or
sightings, fishing activity or effort observations, and separate environmental
assertions or reported environmental context. Source interpretation, advice, and
prediction must remain outside the factual fishing-observation dataset.

`Fishing was slow` is qualitative source interpretation unless a report also
provides actual catch and effort evidence. `No one is fishing today` describes
angler activity, not fish absence. Report silence must never create a negative
catch assertion. A true zero-catch assertion remains unresolved unless a source
explicitly reports zero catch under meaningful observed effort or a later
approved standardized source supports that interpretation.

### Catch, quantity, and measurement remain qualified

Release and harvest are catch dispositions when explicitly supported, not
separate observation types. They must not be inferred from regulations,
citation status, size, or outside knowledge.

Exact counts remain exact only when reported. Qualitative quantities such as a
few, some, lots, hundreds, odd, good numbers, and a ton remain qualitative.
Effort or duration, when reported, remains separate. The `39 Sea Mullet` example
preserves both a count and three hours; it does not authorize a catch-rate
calculation when effort is absent.

Measurements can be exact, approximate, or explicitly estimated. Units and
qualification remain part of the assertion. An estimated weight is not
equivalent to a measured weight.

### Species terms, place, and mode remain source-supported

Every assertion retains its raw source term. Canonical species identity remains
nullable whenever source wording and context do not support an unambiguous
mapping. The encountered terms include drum, puppy drum, Spanish, blue, sea
mullet, sheephead, and trout. Terms with size-class meaning, including puppy,
slot, over-slot, and yearling, retain that raw meaning even when later work can
identify a canonical species.

Spatial scope remains separate from the source. The sample ranged from named
sites such as Ramp 72 and Little Bridge through named local areas and Ocracoke
surf or Pamlico Sound behind Ocracoke to regional district and fishing-mode
summaries. No coordinates or finer scope may be manufactured. Fishing mode is
preserved only when reported.

### Evidence has more than one dimension

The trial supports preserving assertion granularity separately from evidence or
provenance basis:

| Dimension | Supported distinctions |
| --- | --- |
| Assertion granularity | individual catch or event; site summary; regional summary |
| Evidence or provenance basis | measured or weighed individual record; named angler or customer report or submitted photo; source or staff site summary; agency observation or interview synthesis |

A precise individual catch can still come from a selectively curated source.
Bogue Inlet Pier Catch Boards can preserve dated and weighed catches, but are
highlight boards rather than catch-frequency datasets. Source-selection or
coverage bias belongs in source-level provenance or research context, not as an
assertion-level abundance claim.

### Environmental assertions or context remain independent

When a source supports a separate environmental assertion or reports
environmental context, it remains distinct from catch assertions. Whether an
environmental value is observed, measured, predicted, forecast, or otherwise
reported must be stated only when the source establishes it. Report-day
environmental context must not be attached to catches from another date or
unsupported period. The common report and assertion envelope can carry these
concepts, but their detailed treatment remains outside this package.

## Smallest defensible conceptual model

The trial supports one source document or report with zero or more assertions:

```text
source document / report
    -> zero or more assertions
```

The common model must be capable of preserving these concepts when applicable
and supported by the source:

- assertion classification
- raw subject and optional normalized subject or species, which may be unavailable
- temporal scope and precision
- spatial scope and location reference
- fishing mode, which may be unavailable
- optional quantitative and qualitative values
- optional measurement qualification and units
- catch disposition only when explicit
- evidence or provenance basis
- assertion granularity
- source reference and provenance

This is a research finding, not a database schema or final requirements
contract.

## Failed or ambiguous normalization cases

| Case | Why it cannot be flattened |
| --- | --- |
| Page-day environmental values with yesterday's catch | The report and catch have different supported times. |
| Same-day and previous-day catches in one report | Each assertion can have a different temporal scope. |
| CMS page date later than the date stated in the report | Publication time and report-effective date can disagree without either being silently replaced. |
| `No one is fishing today` | It is effort information, not negative fish evidence. |
| `Fishing was slow` or tide advice | Interpretation and advice are not factual catch observations. |
| `drum`, `Spanish`, or `blue` | Raw terminology can be more certain than a canonical species identity. |
| Qualitative quantities | Words such as good numbers cannot become invented counts. |
| Report-day conditions with earlier Bogue catches | Environmental values cannot be retroactively assigned to catch assertions. |
| Exact Bogue Catch Board records | Individual precision does not remove highlight-board selection bias. |
| Surf, sound, charter, and regional reports | A source can contain several distinct places and fishing modes. |

## Limitations and unresolved questions

- This trial does not approve a permanent requirements contract, storage model,
  collector, or retrieval architecture.
- It does not complete source risk classification or make legal conclusions
  about collection.
- It does not resolve a canonical statewide species taxonomy or every ambiguous
  term.
- It does not define numeric abundance, confidence, catch-rate, or absence.
- It leaves detailed environmental assertion or context treatment and true
  zero-catch interpretation for later work.

## Related authority

- [Location-first species-assessment direction](../decisions/0011-location-first-species-assessment-direction.md)
- [Current roadmap](../roadmap.md)
- [Project roadmap](../project-roadmap.md)
