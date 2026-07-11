"""Export Power BI sample CSVs from existing P5 platform artifacts.

This script reads runtime artifacts already produced by ``pipelines/run_platform.py``
(observability reports, quality reports, release gate, schema registry, alerts,
metadata catalog, lineage graph, and gold marts) and flattens them into clean,
flat CSVs under ``powerbi/sample_exports/`` for a downstream Power BI model.

Honesty rules (see powerbi/README.md):
- It never fabricates data. Every CSV is derived from a real platform artifact.
- The platform release gate is platform-level, not per-dataset, so it is exported
  as-is in ``release_gates.csv`` while per-dataset signals live in
  ``dataset_readiness.csv`` and ``dataset_trust_scores.csv``.
- "Incidents" are derived from the operational alert log; there is no separate
  incident store, and the export labels this honestly.
- If a source artifact is missing, the matching CSV is written with documented
  headers only and marked ``empty_source_missing`` in the manifest, rather than
  being faked. Run ``python pipelines/run_platform.py --reset`` first to populate.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "powerbi" / "sample_exports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scalarize(value: Any) -> Any:
    """Flatten lists/dicts to compact strings so a CSV cell stays one value."""
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            return ";".join(str(item) for item in value)
        return json.dumps(value, sort_keys=True)
    return value


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, Any]]) -> int:
    path = EXPORT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: scalarize(row.get(key, "")) for key in fieldnames})
    return len(rows)


# --- Individual exporters -------------------------------------------------
# Each returns (source_label, fieldnames, rows). Missing sources return [] rows.

def export_dataset_trust_scores() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "observability/reports/dataset_trust_scores.json"
    fieldnames = [
        "dataset_name", "trust_score_overall", "trust_score_band", "recommended_action", "reason_codes",
        "comp_readiness", "comp_quality", "comp_freshness", "comp_schema_stability", "comp_slo_compliance",
        "comp_volume_anomaly", "comp_lineage_completeness", "comp_documentation_completeness", "comp_incident_history",
    ]
    payload = read_json(PROJECT_ROOT / source, {})
    rows = []
    for dataset in (payload or {}).get("datasets", []):
        row = {
            "dataset_name": dataset.get("dataset_name"),
            "trust_score_overall": dataset.get("trust_score_overall"),
            "trust_score_band": dataset.get("trust_score_band"),
            "recommended_action": dataset.get("recommended_action"),
            "reason_codes": dataset.get("reason_codes", []),
        }
        for component in dataset.get("score_components", []):
            row[f"comp_{component.get('name')}"] = component.get("score")
        rows.append(row)
    return source, fieldnames, rows


def export_dataset_readiness() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "observability/reports/dataset_readiness.json"
    fieldnames = [
        "dataset_name", "evaluated_at", "row_count", "quality_status", "freshness_status",
        "schema_status", "readiness_score", "readiness_status",
        "comp_has_rows", "comp_quality", "comp_freshness", "comp_schema",
    ]
    rows = []
    for record in read_json(PROJECT_ROOT / source, []) or []:
        components = record.get("component_scores", {})
        rows.append({
            **{key: record.get(key) for key in
               ["dataset_name", "evaluated_at", "row_count", "quality_status", "freshness_status",
                "schema_status", "readiness_score", "readiness_status"]},
            "comp_has_rows": components.get("has_rows"),
            "comp_quality": components.get("quality"),
            "comp_freshness": components.get("freshness"),
            "comp_schema": components.get("schema"),
        })
    return source, fieldnames, rows


def export_release_gates() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "operations/release/release_gate_report.json"
    fieldnames = [
        "evaluated_at", "release_status", "publish_decision",
        "gate_name", "status", "severity", "observed", "expected", "recommended_action",
    ]
    report = read_json(PROJECT_ROOT / source, {}) or {}
    rows = []
    for gate in report.get("gates", []):
        rows.append({
            "evaluated_at": report.get("evaluated_at"),
            "release_status": report.get("release_status"),
            "publish_decision": report.get("publish_decision"),
            "gate_name": gate.get("gate_name"),
            "status": gate.get("status"),
            "severity": gate.get("severity"),
            "observed": gate.get("observed"),
            "expected": gate.get("expected"),
            "recommended_action": gate.get("recommended_action"),
        })
    return source, fieldnames, rows


_RULE_TYPE_PREFIXES = {
    "schema_required_columns": "schema",
    "unique_": "uniqueness",
    "null_rate_": "null",
    "accepted_values_": "accepted_values",
    "non_negative_": "range",
}


def _rule_type(check_name: str) -> str:
    for prefix, rule_type in _RULE_TYPE_PREFIXES.items():
        if check_name == prefix or check_name.startswith(prefix):
            return rule_type
    return "other"


def export_data_quality_results() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "data_quality/reports/*_quality_report.json"
    fieldnames = [
        "dataset_name", "validated_at", "row_count", "check_name", "rule_type",
        "status", "severity", "observed_value", "threshold", "failed_records",
    ]
    rows = []
    for report_path in sorted((PROJECT_ROOT / "data_quality" / "reports").glob("*_quality_report.json")):
        report = read_json(report_path, {})
        for result in report.get("results", []):
            rows.append({
                "dataset_name": report.get("dataset_name"),
                "validated_at": report.get("validated_at"),
                "row_count": report.get("row_count"),
                "check_name": result.get("check_name"),
                "rule_type": _rule_type(str(result.get("check_name", ""))),
                "status": result.get("status"),
                "severity": result.get("severity"),
                "observed_value": result.get("observed_value"),
                "threshold": result.get("threshold"),
                "failed_records": result.get("failed_records"),
            })
    return source, fieldnames, rows


def export_schema_drift_events() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "metadata/schema_registry.json"
    fieldnames = [
        "source_system", "previous_version", "current_version", "status", "breaking",
        "added_columns", "removed_columns", "type_changes", "safe_renames", "detected_at",
    ]
    registry = read_json(PROJECT_ROOT / source, {}) or {}
    rows = [
        {key: event.get(key) for key in fieldnames}
        for event in registry.get("history", [])
    ]
    return source, fieldnames, rows


def export_contract_validations() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "metadata/contract_reports/**/*_contract_report.json"
    fieldnames = [
        "source_system", "dataset_name", "report_file", "status", "violation_count",
        "owner", "criticality_tier", "observed_at", "validated_at",
    ]
    rows = []
    for report_path in sorted((PROJECT_ROOT / "metadata" / "contract_reports").glob("**/*_contract_report.json")):
        report = read_json(report_path, {})
        rows.append({
            "source_system": report.get("source_system"),
            "dataset_name": report.get("dataset_name"),
            "report_file": report_path.name,
            "status": report.get("status"),
            "violation_count": report.get("violation_count"),
            "owner": report.get("owner"),
            "criticality_tier": report.get("criticality_tier"),
            "observed_at": report.get("observed_at"),
            "validated_at": report.get("validated_at"),
        })
    return source, fieldnames, rows


def export_incident_log() -> tuple[str, list[str], list[dict[str, Any]]]:
    # Derived honestly from the operational alert log (no separate incident store exists).
    source = "alerts/alert_log.jsonl"
    fieldnames = [
        "incident_id", "alert_type", "severity", "dataset_name", "source_system",
        "resolution_status", "business_impact", "recommended_action", "timestamp",
    ]
    rows = []
    for alert in read_jsonl(PROJECT_ROOT / source):
        rows.append({
            "incident_id": alert.get("alert_id"),
            "alert_type": alert.get("alert_type"),
            "severity": alert.get("severity"),
            "dataset_name": alert.get("dataset_name"),
            "source_system": alert.get("source_system"),
            "resolution_status": alert.get("resolution_status"),
            "business_impact": alert.get("business_impact"),
            "recommended_action": alert.get("recommended_action"),
            "timestamp": alert.get("timestamp"),
        })
    return source, fieldnames, rows


def export_metadata_catalog() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "metadata/data_catalog.json"
    fieldnames = [
        "dataset_name", "layer", "owner", "source_system", "refresh_frequency",
        "criticality_tier", "business_description", "downstream_usage", "last_refresh", "readiness_status",
    ]
    rows = read_json(PROJECT_ROOT / source, []) or []
    return source, fieldnames, rows


def export_lineage_edges() -> tuple[str, list[str], list[dict[str, Any]]]:
    source = "lineage/lineage_graph.json"
    fieldnames = ["source", "target", "relationship"]
    graph = read_json(PROJECT_ROOT / source, {}) or {}
    return source, fieldnames, list(graph.get("edges", []))


def export_gold_mart_summary() -> tuple[str, list[str], list[dict[str, Any]]]:
    # Derived join: gold row counts + trust band + readiness status per mart.
    source = "gold_layer/*.csv + dataset_trust_scores.json + dataset_readiness.json"
    fieldnames = [
        "dataset_name", "row_count", "trust_score_overall", "trust_score_band",
        "readiness_status", "quality_status", "freshness_status", "schema_status",
    ]
    trust = {
        d.get("dataset_name"): d
        for d in (read_json(PROJECT_ROOT / "observability/reports/dataset_trust_scores.json", {}) or {}).get("datasets", [])
    }
    readiness = {
        r.get("dataset_name"): r
        for r in (read_json(PROJECT_ROOT / "observability/reports/dataset_readiness.json", []) or [])
    }
    rows = []
    for gold_csv in sorted((PROJECT_ROOT / "gold_layer").glob("*.csv")):
        dataset_name = gold_csv.stem
        t = trust.get(dataset_name, {})
        r = readiness.get(dataset_name, {})
        rows.append({
            "dataset_name": dataset_name,
            "row_count": len(read_csv(gold_csv)),
            "trust_score_overall": t.get("trust_score_overall"),
            "trust_score_band": t.get("trust_score_band"),
            "readiness_status": r.get("readiness_status"),
            "quality_status": r.get("quality_status"),
            "freshness_status": r.get("freshness_status"),
            "schema_status": r.get("schema_status"),
        })
    return source, fieldnames, rows


def export_gold_passthrough(dataset_name: str) -> Callable[[], tuple[str, list[str], list[dict[str, Any]]]]:
    def _exporter() -> tuple[str, list[str], list[dict[str, Any]]]:
        source = f"gold_layer/{dataset_name}.csv"
        rows = read_csv(PROJECT_ROOT / source)
        fieldnames = list(rows[0].keys()) if rows else []
        return source, fieldnames, rows
    return _exporter


EXPORTS: dict[str, Callable[[], tuple[str, list[str], list[dict[str, Any]]]]] = {
    "dataset_trust_scores.csv": export_dataset_trust_scores,
    "dataset_readiness.csv": export_dataset_readiness,
    "release_gates.csv": export_release_gates,
    "data_quality_results.csv": export_data_quality_results,
    "schema_drift_events.csv": export_schema_drift_events,
    "contract_validations.csv": export_contract_validations,
    "incident_log.csv": export_incident_log,
    "metadata_catalog.csv": export_metadata_catalog,
    "lineage_edges.csv": export_lineage_edges,
    "gold_mart_summary.csv": export_gold_mart_summary,
    "gold_revenue_analytics.csv": export_gold_passthrough("gold_revenue_analytics"),
    "gold_marketing_attribution.csv": export_gold_passthrough("gold_marketing_attribution"),
}


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_entries = []
    for name, exporter in EXPORTS.items():
        source, fieldnames, rows = exporter()
        if not fieldnames:
            # Passthrough source missing entirely; emit nothing usable but record it.
            status = "empty_source_missing"
            write_csv(name, ["note"], [{"note": f"source artifact missing: {source}"}])
            row_count = 0
        else:
            row_count = write_csv(name, fieldnames, rows)
            status = "written" if row_count else "empty_source_missing"
        manifest_entries.append({"file": name, "source": source, "status": status, "row_count": row_count})
        flag = "" if status == "written" else "  <-- source missing; run the pipeline first"
        print(f"  {name:<34} {row_count:>4} rows  ({status}){flag}")

    manifest = {
        "generated_at": utc_now(),
        "export_dir": str(EXPORT_DIR.relative_to(PROJECT_ROOT)),
        "note": "Outputs are from a local, simulated P5 platform run. No data is "
                "fabricated and no trend/history is synthesized. Run "
                "pipelines/run_platform.py --reset first to populate sources.",
        "sources_used": sorted({e["source"] for e in manifest_entries if e["status"] == "written"}),
        "missing_optional_inputs": [e["file"] for e in manifest_entries if e["status"] != "written"],
        "output_files": [e["file"] for e in manifest_entries],
        "exports": manifest_entries,
        "written_count": sum(1 for e in manifest_entries if e["status"] == "written"),
        "missing_count": sum(1 for e in manifest_entries if e["status"] != "written"),
    }
    (EXPORT_DIR / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote {manifest['written_count']} populated CSVs "
          f"({manifest['missing_count']} missing) to {manifest['export_dir']}/")


if __name__ == "__main__":
    main()
