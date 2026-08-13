# Hosted ingestion operation

The `hosted ingestion and report publication` GitHub Actions workflow runs
from `main` every six
hours (`17 */6 * * *`) and can be started with **Run workflow** on the Actions
page. It continues to ingest and publish forecast state and also ingests
current Jennette's Pier and Sunset Beach Pier fishing reports. The hosted
workflow and the manual fishing observation review workflow share one fixed
concurrency group with cancellation disabled, so canonical-state writers cannot
publish concurrently.

## Azure setup

Create a general-purpose v2 storage account with Standard performance, locally
redundant storage, Hot access tier, hierarchical namespace disabled, anonymous
Blob access disabled, Shared Key authorization disabled, secure transfer
required, and a minimum TLS version of 1.2. Enable Blob soft delete for seven
days and leave Blob versioning disabled.

Create the private container `saltbytes-state` with this layout:

```text
state/saltbytes.duckdb
raw/YYYY/MM/DD/HHMMSSZ_<run_id>/<location_id>_<snapshot_id>.json
recovery/<run_id>/saltbytes.duckdb
recovery/<run_id>/publication-failures.txt
```

`HHMMSSZ` comes from the persisted pipeline run start time in UTC. Existing
run ID only folders remain unchanged. Reporting reads the canonical DuckDB
state and does not depend on either raw folder shape.

Create an Entra application or managed identity for GitHub Actions and add an
OpenID Connect federated credential with:

- issuer: `https://token.actions.githubusercontent.com`
- audience: `api://AzureADTokenExchange`
- subject: `repo:epmelito/SaltBytes:ref:refs/heads/main`

Assign only the `Storage Blob Data Contributor` role at this container scope:

```text
/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Storage/storageAccounts/<storage-account>/blobServices/default/containers/saltbytes-state
```

Set these repository Actions variables (not secrets):

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_STORAGE_ACCOUNT`

No client secret, storage key, connection string, or SAS token is required or
used.

## Publication and recovery

Each runner checks whether `state/saltbytes.duckdb` exists. It initializes a
database only when Azure successfully reports the blob does not exist; a
download or existence-check failure aborts before ingestion.

The runner does not download old raw blobs. It attempts every raw JSON upload
created during the run with overwrite protection and gives each Blob upload at
most three total attempts. It opens the DuckDB file read-only, verifies the
current SaltBytes schema, and requires the latest pipeline run to have a
persisted successful or failed completion state. It also verifies that every raw
snapshot referenced by that run has a safe local path under the configured raw
root and was uploaded successfully. It replaces the canonical database only
when every referenced raw snapshot is durable and validation passes.

When raw or canonical database publication remains incomplete after retries,
the runner leaves canonical state unchanged and attempts to preserve the
validated completed database plus a concise failure manifest under the run's
`recovery/<run_id>/` path. Recovery artifacts are noncanonical evidence: the
workflow never restores or promotes them automatically. Raw blobs that succeed
before a later publication failure remain as acceptable immutable orphans.

The pipeline records partial and failed source outcomes in DuckDB. The workflow
synchronizes after `saltbytes` exits, then returns its original exit status. A
failed pipeline can therefore retain its run record and accepted raw data when
state publication succeeds, while its nonzero status prevents report generation
and Pages deployment.

Fishing observation ingestion is isolated from forecast ingestion and between
report sources. A fetch, parse, or persistence failure preserves prior valid
observation history, records a source-specific failed attempt when possible,
and does not prevent the other report source from being attempted or an
otherwise valid forecast canonical publication. New review candidates are
normal source evolution and do not fail the hosted workflow. Observation
attempt state and outstanding review patterns remain in the canonical DuckDB.
Pipeline Monitoring shows the latest attempt for each source, new and
outstanding pattern counts, and bounded pattern wording and provenance needed
for manual review.

Sunset Beach Pier's report host is the only approved HTTP observation source.
This bounded exception applies to its public, read-only, non-authoritative
fishing report because the host's HTTPS certificate does not match its domain.
It does not disable HTTPS verification, create a reusable downgrade path, or
authorize Sunset report content as environmental pipeline input. All report
content remains untrusted external input.

After a successful pipeline and canonical database publication, the runner:

1. generates the deterministic conditions and operations reports
2. replaces the committed dashboard fixtures with a curated public JSON export
3. builds the locked Observable project
4. copies the build to `site/dashboard/`
5. creates a shared landing page linking all three published outputs
6. uploads the complete `site` directory for the existing Pages deployment job

The stable public paths are:

- <https://epmelito.github.io/SaltBytes/dashboard/>
- <https://epmelito.github.io/SaltBytes/conditions/>
- <https://epmelito.github.io/SaltBytes/operations/>

A failed report, export, dashboard build, artifact upload, or deployment fails
the workflow without rolling back canonical state. GitHub Pages keeps the
previously deployed site available because deployment starts only after the
complete site artifact is generated successfully.

## Manual observation review

Use the `apply fishing observation review` GitHub Actions workflow to apply a
manual decision. The operator supplies a pattern ID from Pipeline Monitoring
and one approved disposition: `irrelevant`, `useful_existing_semantics`, or
`accepted_for_parser`. The workflow restores the latest canonical DuckDB from
Azure, applies the decision through the SaltBytes review command, validates the
result, and replaces canonical state only after those steps succeed. Failed
validation or application publishes nothing.

There are two authorized canonical-state writers: hosted ingestion and
publication, and manual fishing observation review. Both use the
`saltbytes-hosted-ingestion` concurrency group with cancellation disabled, so
neither can overwrite the other's newer state.

Pull request validation installs the committed dashboard lock file and builds
Observable from deterministic fixture JSON. That validation does not authenticate
to Azure or read the hosted DuckDB database.

To recover from a failed hosted ingestion run, inspect its Action log and any run-specific
failure manifest, then correct the source, build, or Azure permission problem
and manually run the workflow from `main`. Do not copy a recovery database or
upload an unvalidated local database over `state/saltbytes.duckdb`; the two
workflows above are the supported canonical publishers. Blob soft delete permits
recovery of a deleted state blob for seven days.
