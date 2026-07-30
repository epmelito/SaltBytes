#!/usr/bin/env bash

# Azure access is kept on the hosted runner; the application uses local paths.
set -uo pipefail

readonly database_path="data/local/saltbytes.duckdb"
readonly raw_data_path="data/local/raw"
readonly database_blob="state/saltbytes.duckdb"

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

publish_raw_snapshots() {
    local raw_file relative_path

    while IFS= read -r -d '' raw_file; do
        relative_path="${raw_file#"$raw_data_path"/}"
        az storage blob upload \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "$AZURE_STORAGE_CONTAINER" \
            --name "raw/$relative_path" \
            --file "$raw_file" \
            --overwrite false \
            --auth-mode login \
            --only-show-errors || return 1
    done < <(find "$raw_data_path" -type f -name '*.json' -print0)
}

validate_database() {
    if [[ ! -f "$database_path" ]]; then
        echo "pipeline did not produce a database file" >&2
        return 1
    fi

    python scripts/validate_hosted_database.py "$database_path"
}

publish_database() {
    az storage blob upload \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --container-name "$AZURE_STORAGE_CONTAINER" \
        --name "$database_blob" \
        --file "$database_path" \
        --overwrite true \
        --auth-mode login \
        --only-show-errors
}

main() {
    local pipeline_status=0
    local publication_status=0

    require_environment || return 1
    restore_database || return 1
    mkdir -p "$raw_data_path"

    saltbytes || pipeline_status=$?

    publish_raw_snapshots || publication_status=$?
    if [[ "$publication_status" -eq 0 ]]; then
        validate_database || publication_status=$?
    fi
    if [[ "$publication_status" -eq 0 ]]; then
        publish_database || publication_status=$?
    fi

    if [[ "$pipeline_status" -ne 0 ]]; then
        return "$pipeline_status"
    fi

    return "$publication_status"
}

main "$@"
