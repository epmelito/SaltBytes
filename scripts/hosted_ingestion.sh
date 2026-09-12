#!/usr/bin/env bash

# Azure access is kept on the hosted runner; the application uses local paths.
set -uo pipefail

readonly database_path="data/local/saltbytes.duckdb"
readonly raw_data_path="data/local/raw"
readonly database_blob="state/saltbytes.duckdb"
readonly publication_attempts=3
readonly publication_retry_delay_seconds=2
readonly artifact_retention_days=90
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

    python scripts/validate_hosted_database.py "$database_path"
}

validate_raw_references() {
    python scripts/validate_hosted_database.py \
        "$database_path" \
        "$raw_data_path" \
        "$published_raw_paths_path" \
        "$raw_reference_failures_path" > /dev/null
}

publish_database() {
    upload_blob "$database_blob" "$database_path" true
}

cleanup_historical_artifacts() {
    local run_id="$1"
    local observed_at cutoff prefix prefix_key listed_blobs inventory_summary
    local required_candidates candidate_path blob_name blob_size canonical_payload_bytes
    local rich_inventory_available
    local soft_deleted_listing soft_deleted_summary
    local artifact_total=0
    local artifact_removed=0
    local artifact_failed=0
    local cleanup_failed=0
    local canonical_payload_status="available"
    local soft_deleted_status="unavailable"
    local soft_deleted_count=0
    local soft_deleted_payload_bytes=0
    local -A inventory_status
    local -A active_count active_bytes candidate_count candidate_bytes
    local -A removed_count removed_bytes failed_count failed_bytes

    for prefix_key in raw recovery; do
        inventory_status[$prefix_key]="unavailable"
        active_count[$prefix_key]=0
        active_bytes[$prefix_key]=0
        candidate_count[$prefix_key]=0
        candidate_bytes[$prefix_key]=0
        removed_count[$prefix_key]=0
        removed_bytes[$prefix_key]=0
        failed_count[$prefix_key]=0
        failed_bytes[$prefix_key]=0
    done

    observed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" || return 1
    cutoff="$(date -u -d "$artifact_retention_days days ago" +%Y-%m-%dT%H:%M:%SZ)" \
        || return 1
    if ! canonical_payload_bytes="$(stat -c %s "$database_path")"; then
        canonical_payload_status="unavailable"
        canonical_payload_bytes=0
        echo "canonical database payload telemetry unavailable: size observation failed" >&2
    fi

    # raw and recovery uploads are immutable, so last modified is their creation age
    for prefix in raw/ recovery/; do
        prefix_key="${prefix%/}"
        candidate_path="data/local/${prefix_key}-cleanup-candidates.bin"
        rich_inventory_available=0
        rm -f -- "$candidate_path"
        if listed_blobs="$(az storage blob list \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "$AZURE_STORAGE_CONTAINER" \
            --prefix "$prefix" \
            --num-results "*" \
            --auth-mode login \
            --output json \
            --only-show-errors)"; then
            if inventory_summary="$(printf '%s' "$listed_blobs" | \
                python -m saltbytes.lifecycle_telemetry \
                    inventory "$prefix" "$cutoff" "$candidate_path")"; then
                IFS=$'\t' read -r \
                    active_count[$prefix_key] active_bytes[$prefix_key] \
                    candidate_count[$prefix_key] candidate_bytes[$prefix_key] \
                    <<< "$inventory_summary"
                inventory_status[$prefix_key]="available"
                rich_inventory_available=1
            else
                echo "rich historical artifact telemetry unavailable: $prefix; using required cleanup listing" >&2
            fi
        else
            echo "rich historical artifact inventory unavailable: $prefix; using required cleanup listing" >&2
        fi

        if [[ "$rich_inventory_available" -eq 1 ]]; then
            while IFS= read -r -d '' blob_name && IFS= read -r -d '' blob_size; do
                if [[ "$blob_name" != "$prefix"* || "$blob_name" == state/* ]]; then
                    echo "refusing lifecycle deletion outside $prefix: $blob_name" >&2
                    cleanup_failed=1
                    break
                fi

                ((artifact_total += 1))
                if az storage blob delete \
                    --account-name "$AZURE_STORAGE_ACCOUNT" \
                    --container-name "$AZURE_STORAGE_CONTAINER" \
                    --name "$blob_name" \
                    --auth-mode login \
                    --only-show-errors; then
                    ((artifact_removed += 1))
                    ((removed_count[$prefix_key] += 1))
                    ((removed_bytes[$prefix_key] += blob_size))
                else
                    ((artifact_failed += 1))
                    ((failed_count[$prefix_key] += 1))
                    ((failed_bytes[$prefix_key] += blob_size))
                    cleanup_failed=1
                    echo "historical artifact deletion failed: $blob_name" >&2
                    break
                fi
            done < "$candidate_path"
        else
            rm -f -- "$candidate_path"
            if ! required_candidates="$(az storage blob list \
                --account-name "$AZURE_STORAGE_ACCOUNT" \
                --container-name "$AZURE_STORAGE_CONTAINER" \
                --prefix "$prefix" \
                --num-results "*" \
                --auth-mode login \
                --query "[?properties.lastModified < '$cutoff'].name" \
                --output tsv \
                --only-show-errors)"; then
                echo "required historical artifact listing failed: $prefix" >&2
                cleanup_failed=1
            else
                while IFS= read -r blob_name; do
                    [[ -z "$blob_name" ]] && continue
                    if [[ "$blob_name" != "$prefix"* || "$blob_name" == state/* ]]; then
                        echo "refusing lifecycle deletion outside $prefix: $blob_name" >&2
                        cleanup_failed=1
                        break
                    fi

                    ((artifact_total += 1))
                    if az storage blob delete \
                        --account-name "$AZURE_STORAGE_ACCOUNT" \
                        --container-name "$AZURE_STORAGE_CONTAINER" \
                        --name "$blob_name" \
                        --auth-mode login \
                        --only-show-errors; then
                        ((artifact_removed += 1))
                    else
                        ((artifact_failed += 1))
                        cleanup_failed=1
                        echo "historical artifact deletion failed: $blob_name" >&2
                        break
                    fi
                done <<< "$required_candidates"
            fi
        fi
        rm -f -- "$candidate_path"
        if [[ "$cleanup_failed" -ne 0 ]]; then
            break
        fi
    done

    if soft_deleted_listing="$(az storage blob list \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --container-name "$AZURE_STORAGE_CONTAINER" \
        --prefix "$database_blob" \
        --include ds \
        --num-results "*" \
        --auth-mode login \
        --output json \
        --only-show-errors)"; then
        if soft_deleted_summary="$(printf '%s' "$soft_deleted_listing" | \
            python -m saltbytes.lifecycle_telemetry \
                soft-deleted-snapshots "$database_blob")"; then
            IFS=$'\t' read -r soft_deleted_count soft_deleted_payload_bytes \
                <<< "$soft_deleted_summary"
            soft_deleted_status="available"
        else
            echo "canonical soft-deleted snapshot telemetry unavailable: invalid listing" >&2
        fi
    else
        echo "canonical soft-deleted snapshot telemetry unavailable: listing failed" >&2
    fi

    local -a soft_deleted_arguments=(--soft-deleted-status "$soft_deleted_status")
    if [[ "$soft_deleted_status" == "available" ]]; then
        soft_deleted_arguments+=(
            --soft-deleted-count "$soft_deleted_count"
            --soft-deleted-payload-bytes "$soft_deleted_payload_bytes"
        )
    fi
    local -a canonical_payload_arguments=(
        --canonical-payload-status "$canonical_payload_status"
    )
    if [[ "$canonical_payload_status" == "available" ]]; then
        canonical_payload_arguments+=(--canonical-payload-bytes "$canonical_payload_bytes")
    fi
    if ! python -m saltbytes.lifecycle_telemetry azure-record \
        --pipeline-run-id "$run_id" \
        --observed-at "$observed_at" \
        --artifact-retention-days "$artifact_retention_days" \
        --cleanup-cutoff "$cutoff" \
        "${canonical_payload_arguments[@]}" \
        --raw-status "${inventory_status[raw]}" \
        --raw-metrics "${active_count[raw]},${active_bytes[raw]},${candidate_count[raw]},${candidate_bytes[raw]},${removed_count[raw]},${removed_bytes[raw]},${failed_count[raw]},${failed_bytes[raw]}" \
        --recovery-status "${inventory_status[recovery]}" \
        --recovery-metrics "${active_count[recovery]},${active_bytes[recovery]},${candidate_count[recovery]},${candidate_bytes[recovery]},${removed_count[recovery]},${removed_bytes[recovery]},${failed_count[recovery]},${failed_bytes[recovery]}" \
        "${soft_deleted_arguments[@]}"; then
        echo "hosted storage lifecycle telemetry unavailable: formatting failed" >&2
    fi

    echo "historical artifact cleanup totals: total=$artifact_total removed=$artifact_removed failed=$artifact_failed"
    [[ "$cleanup_failed" -eq 0 ]]
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
    local cleanup_status="not_attempted"
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

    if ! saltbytes retention --database "$database_path" --json; then
        echo "environmental retention failed; canonical state unchanged" >&2
        return 1
    fi

    if run_id="$(validate_database)"; then
        validation_status="passed"
        echo "retained database validation: passed"
        publish_raw_snapshots
        if ! validate_raw_references || [[ -s "$raw_reference_failures_path" ]]; then
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
            if cleanup_historical_artifacts "$run_id"; then
                cleanup_status="completed"
            else
                cleanup_status="failed"
                publication_status=1
            fi
        else
            canonical_status="failed"
            publication_status=1
        fi
    fi

    if [[ "$publication_status" -ne 0 && "$canonical_status" != "published" ]]; then
        if [[ "$validation_status" == "passed" ]]; then
            publish_recovery \
                "$run_id" "$validation_status" "$canonical_status" || true
        else
            echo "recovery publication status: not attempted; completed run database validation failed"
        fi
    fi

    if [[ "$pipeline_status" -ne 0 ]]; then
        if [[ "$canonical_status" == "published" ]]; then
            echo "final hosted outcome: pipeline failed with status $pipeline_status after canonical state publication" >&2
        elif [[ "$publication_status" -ne 0 ]]; then
            echo "final hosted outcome: pipeline failed with status $pipeline_status and publication incomplete; canonical state unchanged" >&2
        fi
        return "$pipeline_status"
    fi

    if [[ "$cleanup_status" == "failed" ]]; then
        echo "final hosted outcome: canonical state published; historical artifact cleanup failed" >&2
    elif [[ "$publication_status" -ne 0 ]]; then
        echo "final hosted outcome: publication incomplete; canonical state unchanged" >&2
    else
        echo "final hosted outcome: canonical state published"
    fi

    return "$publication_status"
}

main "$@"
