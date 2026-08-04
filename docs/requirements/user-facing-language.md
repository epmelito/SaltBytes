# User-facing language requirements

## Status

Approved project-wide presentation contract.

## Purpose

SaltBytes is built for recreational anglers and other general users, not for an
academic or scientific audience. User-facing text must translate the project's
technical work into clear, natural language that sounds appropriate in everyday
conversation.

Internal research and technical documentation may use specialized terminology
when precision requires it. This contract applies where that material crosses
into the product experience.

## Covered surfaces

This contract applies to text shown through:

- conditions and operations reports
- dashboards and published pages
- CLI output intended to be read by users
- headings, labels, controls, chart legends, table columns, and metric names
- displayed values, units, statuses, and unavailable states
- score, confidence, factor, and condition explanations
- summaries, notices, warnings, limitations, and unknowns
- future recommendations or other user-facing interpretations

Raw data, schemas, field names, logs, test fixtures, internal research, and
technical operations may retain precise internal terminology. They must not be
exposed as default product copy without translation when a clearer user-facing
expression is available.

## Language requirements

User-facing text must:

- use familiar words and natural sentence structure
- favor the wording an informed angler might use in ordinary conversation
- explain necessary technical terms at the point where they matter
- make the main takeaway easy to find before deeper detail
- use labels that describe what a value means to the user, not only how it is
  stored or calculated
- preserve material uncertainty, limitations, provenance, and safety meaning
- distinguish unavailable, unknown, not applicable, and failed data when those
  differences affect interpretation
- remain concise without becoming vague or misleading

User-facing text must not:

- read like a thesis, journal article, data dictionary, or internal operations
  report unless the surface is explicitly intended for technical detail
- use academic or scientific phrasing when an accurate plain-language
  alternative exists
- expose internal field names, enum values, model identifiers, or pipeline terms
  as unexplained product labels
- simplify away uncertainty, source limitations, safety boundaries, or the
  difference between measured, predicted, derived, and unknown information
- make catch, presence, bite, success, or safety claims that the evidence does
  not support

## Layered detail

Plain language does not mean hiding technical evidence. Reports and dashboards
may provide deeper methodology, provenance, and operational detail through
secondary sections, tooltips, expandable content, or dedicated technical views.
The default presentation should first tell a general user what the information
means and why it matters.

Technical terms may remain when no accurate everyday substitute exists. In that
case, define them briefly and consistently instead of replacing them with an
inaccurate simplification.

## Review standard

A user-facing change is not complete only because its values are correct and its
layout renders. Reviewers must also check whether an ordinary recreational
angler can understand the primary labels, values, explanations, warnings, and
unknowns without reading the internal research or data model.

Existing reports and dashboards are not declared compliant by this document.
They should be reviewed and updated through bounded reporting work. This
document records the standard those changes must meet.

## Related governance

- [Project charter](../project-charter.md)
- [Fishing-condition requirements](fishing-conditions.md)
- [Species conditions scoring requirements](species-condition-scoring.md)
