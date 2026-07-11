from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ALLOWED_RENAMES = {
    "ecommerce_transactions": {
        "order_id": "transaction_id",
        "order_value": "amount",
        "order_timestamp": "order_ts",
    },
    "marketing_campaigns": {
        "spend_usd": "spend",
        "channel_name": "channel",
    },
    "customer_behavior": {
        "user_id": "customer_id",
        "event_time": "event_ts",
    },
    "crm_support": {
        "user_id": "customer_id",
    },
}


@dataclass
class SchemaField:
    name: str
    data_type: str
    nullable: bool


@dataclass
class DriftReport:
    source_system: str
    previous_version: int | None
    current_version: int
    fingerprint: str
    status: str
    added_columns: list[str]
    removed_columns: list[str]
    type_changes: dict[str, dict[str, str]]
    safe_renames: dict[str, str]
    breaking: bool
    detected_at: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_column_name(name: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", name.strip()).strip("_").lower()
    return re.sub(r"_+", "_", normalized)


def read_source_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [dict(row) for row in payload["records"]]
        raise ValueError(f"Unsupported JSON shape in {path}")
    if suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
        return records
    raise ValueError(f"Unsupported source extension: {path.suffix}")


def infer_scalar_type(value: Any) -> str:
    if value is None or value == "":
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "decimal"
    text = str(value).strip()
    if text.lower() in {"true", "false"}:
        return "boolean"
    try:
        int(text)
        return "integer"
    except ValueError:
        pass
    try:
        float(text)
        return "decimal"
    except ValueError:
        pass
    for pattern in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            datetime.strptime(text, pattern)
            return "timestamp" if "H" in pattern else "date"
        except ValueError:
            continue
    return "string"


def merge_types(types: Iterable[str]) -> str:
    normalized = {item for item in types if item != "null"}
    if not normalized:
        return "string"
    if normalized == {"integer"}:
        return "integer"
    if normalized <= {"integer", "decimal"}:
        return "decimal"
    if normalized <= {"date", "timestamp"}:
        return "timestamp"
    if len(normalized) == 1:
        return next(iter(normalized))
    return "string"


def infer_schema(records: list[dict[str, Any]]) -> list[SchemaField]:
    values_by_column: dict[str, list[Any]] = {}
    for record in records:
        for key, value in record.items():
            values_by_column.setdefault(normalize_column_name(key), []).append(value)
        missing = set(values_by_column) - {normalize_column_name(key) for key in record}
        for key in missing:
            values_by_column[key].append(None)

    fields = []
    for column in sorted(values_by_column):
        values = values_by_column[column]
        data_type = merge_types(infer_scalar_type(value) for value in values)
        nullable = any(value is None or value == "" for value in values)
        fields.append(SchemaField(column, data_type, nullable))
    return fields


def schema_fingerprint(fields: list[SchemaField]) -> str:
    canonical = json.dumps([asdict(field) for field in fields], sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class SchemaRegistry:
    """Small local schema registry with drift detection and safe rename support."""

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._payload = self._load()

    def _load(self) -> dict[str, Any]:
        if self.registry_path.exists():
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        return {"sources": {}, "history": []}

    def _save(self) -> None:
        self.registry_path.write_text(json.dumps(self._payload, indent=2), encoding="utf-8")

    def register(self, source_system: str, records: list[dict[str, Any]]) -> DriftReport:
        fields = infer_schema(records)
        fingerprint = schema_fingerprint(fields)
        previous = self._payload["sources"].get(source_system)
        previous_fields = previous.get("fields", []) if previous else []
        previous_version = previous.get("schema_version") if previous else None
        status, added, removed, type_changes, safe_renames, breaking = self._compare(
            source_system=source_system,
            previous_fields=previous_fields,
            current_fields=[asdict(field) for field in fields],
        )
        current_version = previous_version or 0
        if previous is None or previous.get("fingerprint") != fingerprint:
            current_version += 1

        report = DriftReport(
            source_system=source_system,
            previous_version=previous_version,
            current_version=current_version,
            fingerprint=fingerprint,
            status=status,
            added_columns=added,
            removed_columns=removed,
            type_changes=type_changes,
            safe_renames=safe_renames,
            breaking=breaking,
            detected_at=utc_now(),
        )

        self._payload["sources"][source_system] = {
            "schema_version": current_version,
            "fingerprint": fingerprint,
            "fields": [asdict(field) for field in fields],
            "updated_at": report.detected_at,
        }
        self._payload["history"].append(asdict(report))
        self._save()
        return report

    def _compare(
        self,
        source_system: str,
        previous_fields: list[dict[str, Any]],
        current_fields: list[dict[str, Any]],
    ) -> tuple[str, list[str], list[str], dict[str, dict[str, str]], dict[str, str], bool]:
        previous_by_name = {field["name"]: field for field in previous_fields}
        current_by_name = {field["name"]: field for field in current_fields}
        added = sorted(set(current_by_name) - set(previous_by_name))
        removed = sorted(set(previous_by_name) - set(current_by_name))
        safe_renames: dict[str, str] = {}

        allowed = ALLOWED_RENAMES.get(source_system, {})
        for new_name, canonical_name in allowed.items():
            if new_name in added and canonical_name in removed:
                safe_renames[new_name] = canonical_name
        for new_name, canonical_name in safe_renames.items():
            if new_name in added:
                added.remove(new_name)
            if canonical_name in removed:
                removed.remove(canonical_name)

        type_changes: dict[str, dict[str, str]] = {}
        for name in sorted(set(previous_by_name) & set(current_by_name)):
            previous_type = previous_by_name[name]["data_type"]
            current_type = current_by_name[name]["data_type"]
            if previous_type != current_type:
                type_changes[name] = {"previous": previous_type, "current": current_type}

        if not previous_fields:
            return "new_schema", added, removed, type_changes, safe_renames, False
        breaking = bool(removed or type_changes)
        if breaking:
            status = "breaking_drift"
        elif added or safe_renames:
            status = "compatible_evolution"
        else:
            status = "unchanged"
        return status, added, removed, type_changes, safe_renames, breaking
