"""Read-only administration projections. Never expose task payloads or provider text."""

from datetime import UTC, datetime

from .models import AdministrationDiagnostics, ImportDiagnostic, JobCounts, JobInfo

# An allowlist, rather than a format check: even snake_case provider text could be secret.
# Unknown future errors retain a useful failure state without echoing their contents.
PUBLIC_ERRORS = frozenset(
    {
        "ai_authentication_failed",
        "ai_connection_failed",
        "ai_model_or_endpoint_not_found",
        "ai_request_rejected",
        "ai_content_blocked",
        "ai_generation_failed",
        "ai_generation_interrupted",
        "ai_configuration_changed_review_consent",
        "ai_input_format_unsupported",
        "ai_timeout",
        "ai_content_disclosure_consent_required",
        "ai_content_too_large",
        "ai_incomplete_recipe_review_manually",
        "ai_invalid_response",
        "ai_not_configured",
        "ai_output_incomplete",
        "ai_provider_failed",
        "ai_rate_limited",
        "ai_request_limit",
        "ai_response_too_large",
        "ai_schema_validation_failed",
        "bring_capability_unverified",
        "bring_configuration_changed",
        "bring_uuid_not_supported",
        "bring_write_not_confirmed",
        "bring_verification_unsafe",
        "bring_verification_baseline_changed",
        "bring_verification_timeout",
        "bring_verification_missing",
        "bring_connection_failed",
        "bring_list_not_found",
        "bring_list_not_selected",
        "bring_item_identity_invalid",
        "bring_not_configured",
        "invalid_extracted_recipe",
        "job_processing_failed",
        "push_network_failed",
        "push_provider_rejected",
        "push_rate_limited",
        "push_session_expired",
        "push_subscription_expired",
        "source_address_forbidden",
        "source_content_type_unsupported",
        "source_dns_failed",
        "source_encoding_unsupported",
        "source_network_failed",
        "source_redirect_invalid",
        "source_redirect_limit",
        "source_resource_limit",
        "source_timeout",
        "source_too_large",
        "source_unavailable_use_supplied_text",
        "source_url_forbidden",
        "structured_recipe_not_found_use_manual_entry",
        "unknown_job_kind",
    }
)


def public_error(code: str | None) -> str | None:
    if code is None:
        return None
    return code if code in PUBLIC_ERRORS else "operation_failed"


def recent_jobs(db, limit: int = 100, state: str | None = None) -> list[JobInfo]:
    where = " WHERE state=?" if state is not None else ""
    parameters = (state, limit) if state is not None else (limit,)
    rows = db.execute(
        "SELECT id,kind,state,attempts,error_code,available_at FROM background_job"
        + where
        + " ORDER BY created_at DESC,id DESC LIMIT ?",
        parameters,
    )
    return [
        JobInfo(
            id=row["id"],
            kind=row["kind"]
            if row["kind"] in ("recipe.import", "shopping.reconcile", "bring.verify")
            else "unknown",
            state=row["state"],
            attempts=row["attempts"],
            error_code=public_error(row["error_code"]),
            available_at=row["available_at"],
        )
        for row in rows
    ]


def diagnostics(database, limit: int = 20) -> AdministrationDiagnostics:
    with database.connect() as db:
        # One read snapshot; queued/running counts and recent rows describe the same state.
        db.execute("BEGIN")
        counts = {
            row["state"]: row["total"]
            for row in db.execute(
                "SELECT state,COUNT(*) AS total FROM background_job GROUP BY state"
            )
        }
        jobs = recent_jobs(db, limit)
        imports = [
            ImportDiagnostic(
                id=row["id"],
                state=row["state"]
                if row["state"] in ("queued", "preview", "needs_input", "confirmed", "cancelled")
                else "unknown",
                error_code=public_error(row["error_code"]),
                created_at=row["created_at"],
            )
            for row in db.execute(
                "SELECT id,state,error_code,created_at FROM import_draft"
                " ORDER BY created_at DESC,id DESC LIMIT ?",
                (limit,),
            )
        ]
        captured = datetime.now(UTC)
    return AdministrationDiagnostics(
        captured_at=captured,
        job_counts=JobCounts(**counts),
        recent_jobs=jobs,
        recent_imports=imports,
    )
