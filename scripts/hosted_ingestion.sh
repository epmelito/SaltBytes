#!/usr/bin/env bash

# Azure access is kept on the hosted runner; the application uses local paths.
set -uo pipefail

readonly database_path="data/local/saltbytes.duckdb"
readonly raw_data_path="data/local/raw"
readonly database_blob="state/saltbytes.duckdb"
readonly publication_attempts=3
readonly publication_retry_delay_seconds=2
readonly published_raw_paths_path="data/local/published-raw-paths.bin"
readonly raw_reference_failures_path="data/local/raw-reference-failures.txt"

raw_total=0
raw_published=0
raw_failed=0
failed_raw_blobs=()

require_environment() {
    local name

    for name in AZURE_STORAGE_ACCOUNT AZURE_STORAGE_CONTAINER; do
        if [[ -z "${!name:-}" ]]; then
            echo "required environment variable $name is not set" >&2
            return 1
        fi
    done
}

restore_database() {
    local exists

    exists="$(az storage blob exists \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --container-name "$AZURE_STORAGE_CONTAINER" \
        --name "$database_blob" \
        --auth-mode login \
        --query exists \
        --output tsv)" || return 1

    if [[ "$exists" == "true" ]]; then
        mkdir -p "$(dirname "$database_path")"
        az storage blob download \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "$AZURE_STORAGE_CONTAINER" \
            --name "$database_blob" \
            --file "$database_path" \
            --auth-mode login \
            --no-progress \
            --only-show-errors
    elif [[ "$exists" != "false" ]]; then
        echo "unexpected database existence result: $exists" >&2
        return 1
    fi
}

upload_blob() {
    local blob_name="$1"
    local file_path="$2"
    local overwrite="$3"
    local attempt status

    for ((attempt = 1; attempt <= publication_attempts; attempt++)); do
        if az storage blob upload \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "$AZURE_STORAGE_CONTAINER" \
            --name "$blob_name" \
            --file "$file_path" \
            --overwrite "$overwrite" \
            --auth-mode login \
            --only-show-errors; then
            return 0
        else
            status=$?
        fi

        echo "blob publication failed: $blob_name (attempt $attempt/$publication_attempts)" >&2
        if [[ "$attempt" -lt "$publication_attempts" ]]; then
            sleep "$publication_retry_delay_seconds"
        fi
    done

    return "$status"
}

publish_raw_snapshots() {
    local raw_file relative_path blob_name

    while IFS= read -r -d '' raw_file; do
        relative_path="${raw_file#"$raw_data_path"/}"
        blob_name="raw/$relative_path"
        ((raw_total += 1))
        if upload_blob "$blob_name" "$raw_file" false; then
            ((raw_published += 1))
            printf '%s\0' "$raw_file" >> "$published_raw_paths_path"
        else
            ((raw_failed += 1))
            failed_raw_blobs+=("$blob_name")
        fi
    done < <(find "$raw_data_path" -type f -name '*.json' -print0)

    echo "raw publication totals: total=$raw_total published=$raw_published failed=$raw_failed"
}

validate_database() {
    if [[ ! -f "$database_path" ]]; then
        echo "pipeline did not produce a database file" >&2
        return 1
    fi

    python scripts/validate_hosted_database.py \
        "$database_path" \
        "$raw_data_path" \
        "$published_raw_paths_path" \
        "$raw_reference_failures_path"
}

publish_database() {
    upload_blob "$database_blob" "$database_path" true
}

write_failure_manifest() {
    local manifest_path="$1"
    local run_id="$2"
    local validation_status="$3"
    local canonical_status="$4"
    local blob_name

    {
        printf 'run_id=%s\n' "$run_id"
        printf 'raw_total=%s\n' "$raw_total"
        printf 'raw_published=%s\n' "$raw_published"
        printf 'raw_failed=%s\n' "$raw_failed"
        printf 'database_validation=%s\n' "$validation_status"
        printf 'canonical_database=%s\n' "$canonical_status"
        for blob_name in "${failed_raw_blobs[@]}"; do
            printf 'failed_raw_blob=%s\n' "$blob_name"
        done
        if [[ -f "$raw_reference_failures_path" ]]; then
            cat "$raw_reference_failures_path"
        fi
    } > "$manifest_path"
}

publish_recovery() {
    local run_id="$1"
    local validation_status="$2"
    local canonical_status="$3"
    local recovery_prefix="recovery/$run_id"
    local manifest_path="data/local/publication-failure-manifest.txt"
    local database_status="failed"
    local manifest_status="failed"

    write_failure_manifest \
        "$manifest_path" "$run_id" "$validation_status" "$canonical_status"

    if upload_blob \
        "$recovery_prefix/saltbytes.duckdb" "$database_path" false; then
        database_status="published"
    fi
    if upload_blob \
        "$recovery_prefix/publication-failures.txt" "$manifest_path" false; then
        manifest_status="published"
    fi

    echo "recovery publication status: database=$database_status manifest=$manifest_status"

    [[ "$database_status" == "published" && "$manifest_status" == "published" ]]
}

main() {
    local pipeline_status=0
    local publication_status=0
    local validation_status="failed"
    local canonical_status="not_attempted"
    local run_id=""

    require_environment || return 1
    restore_database || return 1
    mkdir -p "$raw_data_path"
    : > "$published_raw_paths_path"
    : > "$raw_reference_failures_path"

    saltbytes || pipeline_status=$?

    if ! saltbytes observations ingest-current --database "$database_path"; then
        echo "fishing observation ingestion had source failures; source outcomes are shown above" >&2
    fi

    publish_raw_snapshots
    if run_id="$(validate_database)"; then
        validation_status="passed"
        if [[ -s "$raw_reference_failures_path" ]]; then
            publication_status=1
        fi
    else
        publication_status=1
    fi

    if [[ "$raw_failed" -ne 0 || -s "$raw_reference_failures_path" ]]; then
        publication_status=1
    elif [[ "$validation_status" == "passed" ]]; then
        if publish_database; then
            canonical_status="published"
        else
            canonical_status="failed"
            publication_status=1
        fi
    fi

    if [[ "$publication_status" -ne 0 && "$validation_status" == "passed" ]]; then
        publish_recovery \
            "$run_id" "$validation_status" "$canonical_status" || true
    elif [[ "$publication_status" -ne 0 ]]; then
        echo "recovery publication status: not attempted; completed run database validation failed"
    fi

    if [[ "$pipeline_status" -ne 0 ]]; then
        if [[ "$publication_status" -ne 0 ]]; then
            echo "final hosted outcome: pipeline failed with status $pipeline_status and publication incomplete; canonical state unchanged" >&2
        else
            echo "final hosted outcome: pipeline failed with status $pipeline_status after canonical state publication" >&2
        fi
        return "$pipeline_status"
    fi

    if [[ "$publication_status" -ne 0 ]]; then
        echo "final hosted outcome: publication incomplete; canonical state unchanged" >&2
    else
        echo "final hosted outcome: canonical state published"
    fi

    return "$publication_status"
}

main "$@"
