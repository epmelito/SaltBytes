# Fishing observation requirements

## Status

Approved product contract for representing fishing observations in SaltBytes.

These requirements define source-independent observation semantics. They do not approve a collector, source, database schema, storage layout, ingestion schedule, species taxonomy, assessment method, or user interface.

The contract is grounded in the completed [fishing observation contract trial](../research/fishing-observation-contract-trial.md). Production-source suitability remains governed separately by the [source suitability assessment](../research/fishing-observation-source-suitability.md).

## Purpose

SaltBytes may use recent fishing observations as one input to location-first species assessments.

The observation contract must preserve what a source actually supports without inventing temporal or geographic precision, species identity, quantity, fish absence, environmental relationships, or evidentiary certainty.

Recent observations are evidence of reported fishing activity or conditions. They are not, by themselves, proof that a species is currently targetable at a location.

## Semantic model

A source report or document may support zero or more assertions.

```text
source report / document
    -> zero or more assertions
```

Assertions from the same report may differ in time, place, subject, fishing mode, evidence basis, and meaning.

A report may mix factual observations with interpretation, advice, or prediction. Those meanings must remain distinguishable rather than being flattened into one observation.

This model is semantic. It does not prescribe database tables, fields, records, or parser structure.

## Normalization rule

Normalization may reduce ambiguity only when the source supports that reduction.

It must never increase temporal, geographic, species, quantitative, measurement, or evidentiary precision beyond the source.

Raw source wording must remain recoverable when it carries material meaning or uncertainty.

## Report provenance and time

SaltBytes must preserve enough provenance to identify the source material from which an assertion was derived.

Retrieval time is provenance only. It must not substitute for publication time, report-effective time, or observation time.

Where supported, the contract must keep distinct:

- page or publication time
- report-effective time or date
- assertion observation time or observation window

Sources may express time as an exact date or time, a relative date, a daypart, an approximate period, or an unresolved time.

SaltBytes must preserve that level of precision. Approximate phrases must not be converted into fabricated exact intervals.

## Assertion meaning

The contract must distinguish materially different kinds of source statements.

It must support distinguishing:

- catch observations
- fish or bait presence or sightings
- fishing activity or effort observations
- environmental assertions or reported environmental context
- source interpretation
- advice
- prediction

Interpretation, advice, and prediction must not silently enter factual observation history.

Statements such as `fishing was slow` are interpretation unless the source separately provides factual catch or effort evidence.

## Species and subject terminology

The raw subject terminology reported by the source must be preserved.

A normalized species identity may be added only when the source wording and context support an unambiguous mapping. Normalized identity must remain unavailable when that mapping is not justified.

Raw size or class terminology such as `puppy`, `slot`, `over-slot`, or `yearling` must retain its source meaning. SaltBytes must not convert those terms into biological age or life-stage facts without a separately approved rule.

This contract does not define a statewide species taxonomy.

## Geography and fishing mode

Geographic scope must remain no more precise than the source.

The contract must distinguish materially different scopes including:

- exact site
- named local or nearby area
- regional area

Fishing mode must be preserved when supported by the source.

SaltBytes must not manufacture coordinates, exact-site identity, or a narrower fishing context from broader source language.

Exact-site, local, and regional observations must not be treated as equivalent merely because they concern the same species.

## Quantity, effort, and measurements

Exact numeric quantities may be preserved only when the source reports an actual number.

Qualitative quantity language must remain qualitative rather than being converted into invented counts.

Effort or duration must remain distinct from catch quantity when reported. SaltBytes must not manufacture catch rates when required effort information is absent.

Terms such as `slow` must not be converted into zero catch or another numeric observation.

Reported measurements must retain their units and any material qualification. Approximate or estimated measurements must not become indistinguishable from exact measured values.

## Catch disposition

Release or harvest is a property of a catch when explicitly supported by the source.

Disposition must not be inferred from regulations, species, size, photographs, citation status, or assumed angler behavior.

Unknown disposition must remain unknown.

## Evidence distinctions

The contract must preserve assertion granularity separately from evidence or provenance basis.

Material assertion granularities include:

- individual catch or event
- site summary
- regional summary

Material evidence bases may include:

- measured or weighed individual record
- named angler or customer report or submitted evidence
- source or staff site summary
- agency observation or interview synthesis

These distinctions must not be collapsed into a single numeric confidence value.

A precise individual observation may still come from a selectively curated source. Source coverage or selection bias must therefore remain separate from assertion-level abundance or precision.

## Negative evidence

Report silence is not evidence of species absence.

SaltBytes must preserve these distinctions:

- non-mention means unknown
- no observed fishing activity does not mean fish were absent
- `slow` is interpretation, not zero catch

The ordinary observation contract must not create negative catch observations from silence.

True zero-catch evidence remains narrow. It requires an explicit source statement supported by meaningful observed effort or another separately approved standardized observation method.

## Environmental context

Environmental information reported alongside fishing observations must remain semantically separate from catch assertions unless the source supports the relevant temporal and spatial relationship.

SaltBytes must not attach report-day conditions to catches from another day merely because both appear in the same report.

Whether environmental information is observed, measured, forecast, predicted, or otherwise reported may be stated only when the source establishes that meaning.

Detailed environmental-observation requirements remain outside this contract.

## Interpretation boundaries

This contract does not authorize SaltBytes to infer:

- fish absence from non-mention
- abundance from qualitative language
- catch rate without supported effort
- canonical species identity from ambiguous terminology
- exact location from broader geographic language
- biological life stage from informal size terminology
- environmental cause from co-occurrence in a report
- numeric confidence from source type or assertion detail
- current targetability from recent observations alone

Source suitability and observation meaning are separate authorities. A source being suitable for production ingestion does not strengthen the meaning of an individual assertion, and an informative source does not automatically make it suitable for automated production use.

## Relationship to location-first assessment

Fishing observations are one evidence input to the approved location-first species-assessment direction.

Later assessment work may combine them with species knowledge, site context, and forecast conditions.

This contract does not define:

- species ranking
- catch probability
- abundance estimates
- assessment weighting
- fishing opportunity scores
- final user-facing presentation

Those require separate evidence and approval.

## Related authority

- [Location-first species-assessment direction](../decisions/0011-location-first-species-assessment-direction.md)
- [Fishing observation contract trial](../research/fishing-observation-contract-trial.md)
- [Fishing observation source suitability assessment](../research/fishing-observation-source-suitability.md)
- [Fishing-condition requirements](fishing-conditions.md)
- [Current roadmap](../roadmap.md)
