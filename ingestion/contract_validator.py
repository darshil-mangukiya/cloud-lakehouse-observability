from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion.schema_registry import infer_schema, normalize_column_name


TYPE_COMPATIBILITY = {
    "string": {"string", "integer", "decimal", "boolean", "date", "timestamp"},
    "decimal": {"decimal", "integer"},
    "integer": {"integer"},
    "timestamp": {"timestamp", "date"},
    "date": {"date"},
    "boolean": {"boolean"},
}


@dataclass
class ContractViolation:
    check_name: str
    severity: str
    observed_value: Any
    expected_value: Any
    message: str
    action: str
    quarantine_recommended: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_contracts(path: Path) -> dict[str, dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_columns(source_contract: dict[str, Any], records: list[dict[str, Any]]) -> set[str]:
    renames = source_contract.get("allowed_renames", {})
    columns = set()
    for record in records:
        for raw_column in record:
            column = normalize_column_name(raw_column)
            columns.add(renames.get(column, column))
    return columns


def canonical_record(source_contract: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    renames = source_contract.get("allowed_renames", {})
    canonical = {}
    for raw_column, value in record.items():
        column = normalize_column_name(raw_column)
        canonical[renames.get(column, column)] = value
    return canonical


def canonical_records(source_contract: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [canonical_record(source_contract, record) for record in records]


def is_null(value: Any) -> bool:
    return value is None or value == ""


def compatible_type(expected: str, observed: str) -> bool:
    return observed in TYPE_COMPATIBILITY.get(expected, {expected})


def infer_canonical_types(records: list[dict[str, Any]]) -> dict[str, str]:
    return {field.name: field.data_type for field in infer_schema(records)}


def contract_status(violations: list[ContractViolation], quarantine_on_failure: bool) -> str:
    if any(violation.quarantine_recommended for violation in violations):
        return "QUARANTINE"
    if any(violation.severity == "critical" for violation in violations):
        return "QUARANTINE" if quarantine_on_failure else "FAIL"
    if any(violation.severity == "high" for violation in violations):
        return "FAIL"
    if violations:
        return "WARNING"
    return "PASS"


def validate_contract(
    source_system: str,
    records: list[dict[str, Any]],
    contracts_path: Path,
    observed_at: str | None = None,
    validation_time: str | None = None,
) -> dict[str, Any]:
    contracts = load_contracts(contracts_path)
    contract = contracts[source_system]
    canonical = canonical_records(contract, records)
    columns = canonical_columns(contract, records)
    expected_schema = contract.get("accepted_data_types") or contract.get("expected_schema", {})
    expected_columns = set(contract.get("required_columns", [])) | set(contract.get("optional_columns", []))
    violations: list[ContractViolation] = []

    missing_required = sorted(set(contract["required_columns"]) - columns)
    if missing_required:
        violations.append(
            ContractViolation(
                check_name="required_columns_present",
                severity="critical",
                observed_value=sorted(columns),
                expected_value=contract["required_columns"],
                message=f"Missing required columns: {', '.join(missing_required)}",
                action="Quarantine the load or update the contract after source-owner approval.",
                quarantine_recommended=contract.get("quarantine_on_failure", False),
            )
        )

    unexpected_columns = sorted(columns - expected_columns)
    if unexpected_columns:
        compatibility_mode = contract.get("schema_compatibility_mode", "backward_compatible")
        severity = "medium" if compatibility_mode in {"backward_compatible", "fully_compatible"} else "high"
        violations.append(
            ContractViolation(
                check_name="unexpected_columns",
                severity=severity,
                observed_value=unexpected_columns,
                expected_value=sorted(expected_columns),
                message=f"New non-contracted columns observed: {', '.join(unexpected_columns)}",
                action="Log as additive evolution and add metadata if downstream consumers need the fields.",
            )
        )

    primary_key = contract["primary_key"]
    pk_values = [str(record.get(primary_key, "")).strip() for record in canonical]
    missing_pk_count = sum(1 for value in pk_values if not value)
    if missing_pk_count:
        violations.append(
            ContractViolation(
                check_name="primary_key_not_null",
                severity="critical",
                observed_value=missing_pk_count,
                expected_value=0,
                message=f"{missing_pk_count} records are missing primary key {primary_key}",
                action="Reject or quarantine records without durable primary keys.",
                quarantine_recommended=contract.get("quarantine_on_failure", False),
            )
        )

    duplicate_values = sorted(value for value, count in Counter(value for value in pk_values if value).items() if count > 1)
    if duplicate_values:
        violations.append(
            ContractViolation(
                check_name="primary_key_unique",
                severity="critical",
                observed_value=duplicate_values,
                expected_value="all primary key values unique",
                message=f"Duplicate primary key values detected for {primary_key}: {', '.join(duplicate_values)}",
                action="Route duplicate records to failed-record handling before silver promotion.",
                quarantine_recommended=contract.get("quarantine_on_failure", False),
            )
        )

    row_count = len(canonical)
    if row_count:
        for column, threshold in contract.get("null_thresholds", {}).items():
            null_count = sum(1 for record in canonical if is_null(record.get(column)))
            null_ratio = round(null_count / row_count, 4)
            if null_ratio > float(threshold):
                violations.append(
                    ContractViolation(
                        check_name=f"null_threshold_{column}",
                        severity="critical" if column in contract.get("required_columns", []) else "high",
                        observed_value=null_ratio,
                        expected_value=f"<= {threshold}",
                        message=f"{column} null ratio {null_ratio} exceeded contract threshold {threshold}",
                        action="Investigate source extract completeness and quarantine if required-field nulls spike.",
                        quarantine_recommended=contract.get("quarantine_on_failure", False)
                        and column in contract.get("required_columns", []),
                    )
                )

    observed_types = infer_canonical_types(canonical) if canonical else {}
    for column, expected_type in expected_schema.items():
        observed_type = observed_types.get(column)
        if observed_type and not compatible_type(expected_type, observed_type):
            violations.append(
                ContractViolation(
                    check_name=f"type_validation_{column}",
                    severity="critical",
                    observed_value=observed_type,
                    expected_value=expected_type,
                    message=f"{column} type changed from expected {expected_type} to observed {observed_type}",
                    action="Treat as breaking schema evolution until mapper, dbt model, and contract are reviewed.",
                    quarantine_recommended=contract.get("quarantine_on_failure", False),
                )
            )

    for column, allowed_values in contract.get("accepted_values", {}).items():
        allowed = {str(value).lower() for value in allowed_values}
        bad_values = sorted(
            {
                str(record.get(column))
                for record in canonical
                if record.get(column) not in (None, "") and str(record.get(column)).lower() not in allowed
            }
        )
        if bad_values:
            violations.append(
                ContractViolation(
                    check_name=f"accepted_values_{column}",
                    severity="high",
                    observed_value=bad_values,
                    expected_value=sorted(allowed),
                    message=f"Unexpected values in {column}: {', '.join(bad_values)}",
                    action="Confirm whether values are valid business states or upstream data defects.",
                )
            )

    validation_ts = parse_timestamp(validation_time) or datetime.now(timezone.utc)
    observed_ts = parse_timestamp(observed_at)
    if observed_ts:
        age_minutes = (validation_ts - observed_ts).total_seconds() / 60
        expected_minutes = int(contract.get("freshness_sla_minutes", contract.get("freshness_sla_hours", 24) * 60))
        if age_minutes > expected_minutes:
            violations.append(
                ContractViolation(
                    check_name="freshness_sla",
                    severity="high",
                    observed_value=round(age_minutes, 2),
                    expected_value=f"<= {expected_minutes} minutes",
                    message=f"Source file age {round(age_minutes, 2)} minutes exceeded freshness SLA.",
                    action="Confirm upstream extraction cadence and backfill missing source partitions.",
                )
            )

    safe_renames = {
        raw_name: canonical_name
        for raw_name, canonical_name in contract.get("allowed_renames", {}).items()
        if any(normalize_column_name(raw_name) in {normalize_column_name(column) for column in record} for record in records)
    }
    status = contract_status(violations, bool(contract.get("quarantine_on_failure", False)))

    return {
        "source_system": source_system,
        "dataset_name": contract.get("dataset_name", source_system),
        "validated_at": utc_now(),
        "observed_at": observed_at,
        "owner": contract["owner"],
        "business_domain": contract.get("business_domain"),
        "business_criticality": contract.get("business_criticality"),
        "criticality_tier": contract["criticality_tier"],
        "freshness_sla_minutes": contract.get("freshness_sla_minutes"),
        "freshness_sla_hours": contract.get("freshness_sla_hours"),
        "schema_compatibility_mode": contract.get("schema_compatibility_mode"),
        "downstream_dependencies": contract.get("downstream_dependencies", contract.get("downstream_gold_datasets", [])),
        "downstream_gold_datasets": contract.get("downstream_gold_datasets", []),
        "row_count": row_count,
        "observed_columns": sorted(columns),
        "expected_columns": sorted(expected_columns),
        "safe_renames_applied": safe_renames,
        "status": status,
        "outcome": status,
        "violation_count": len(violations),
        "violations": [asdict(violation) for violation in violations],
    }


def write_contract_report(report: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path
