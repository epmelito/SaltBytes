# Current roadmap

This roadmap owns the current SaltBytes delivery sequence and the next few
pieces of work. See the [project roadmap](project-roadmap.md) for the larger
project direction and completed phases.

## Current position

SaltBytes has completed its coastal data foundation, hosted publishing,
research backed fishing context, and the first published species conditions
score.

Spanish mackerel results are calculated when dashboard data is exported and are
published through the dashboard. They are not stored in the database. SaltBytes
does not provide catch probability, ranked fishing windows, or an overall
fishing conditions score.

The project is now finishing the reporting phase so the public Conditions view
and the technical Operations views are clear, consistent, and easy to inspect.

## Next work

### 1. Make source history easy to follow

Redesign Data Provenance so a reader can follow published information from its
original source through SaltBytes and into the dashboard.

The page should lead with a clear result and keep exact identifiers and the full
source history available when someone needs more detail.

### 2. Add realistic dashboard test data

Add a fixed dataset with enough saved runs, locations, forecast times, changes,
and missing values to expose layout and browser problems that the small sample
data cannot reveal.

The dataset should support repeatable visual review without depending on the
latest hosted run.

### 3. Decide whether Operations needs shared detail pages

After the three Operations pages are complete, check whether shared views for
runs, sources, failures, forecast updates, or source records would remove real
duplication and improve investigation.

Do not build shared detail pages unless the completed pages show a clear need.

### 4. Finish desktop reporting polish

Review the landing page and every maintained dashboard route as one product.

Complete the shared light and dark themes, route consistency, everyday
language, keyboard access, focus states, spacing, charts, tables, controls, and
empty or unavailable states. Keep mobile refinement and static HTML report
redesign outside this phase.

## After this phase

The likely next direction is to add conditions scores for more reviewed
species. The next species and its method still require a separate decision and
bounded work package.

Fishing opportunity comparisons and an overall conditions score remain later
work. Their methods will not be selected until several species models exist.
