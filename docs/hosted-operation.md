# Hosted ingestion operation

The `hosted ingestion` GitHub Actions workflow runs from `main` every six
hours (`17 */6 * * *`) and can be started with **Run workflow** on the Actions
page. One fixed concurrency group does not cancel in-progress work, so
scheduled and manual runs cannot publish state concurrently.

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

The runner does not download old raw blobs. It uploads raw JSON created during
the run with overwrite protection. Once raw publication succeeds, it opens the
DuckDB file read-only, verifies the current SaltBytes schema, and requires the
latest pipeline run to have a persisted successful or failed completion state
before replacing the database blob. This keeps the current cloud database
canonical if raw publication, validation, or database upload fails. Raw blobs
that succeed before a later database failure remain as acceptable immutable
orphans.

The pipeline records partial and failed source outcomes in DuckDB. The workflow
synchronizes after `saltbytes` exits, then returns its original exit status. A
failed pipeline can therefore retain its run record and accepted raw data when
publication succeeds.

To recover from a failed run, inspect its Action log, correct the source or
Azure permission problem, and manually run the workflow from `main`. Do not
upload an unvalidated local database over `state/saltbytes.duckdb`; the
workflow is the supported publisher. Blob soft delete permits recovery of a
deleted state blob for seven days.
