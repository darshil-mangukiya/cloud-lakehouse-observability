from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def product_status(blockers: list[str], warnings: list[str]) -> str:
    if blockers:
        return "blocked"
    if warnings:
        return "conditional"
    return "certified"


def certify_data_products(project_root: Path) -> dict[str, Any]:
    manifest = read_json(project_root / "metadata/data_products/data_product_manifest.json", {"data_products": []})
    readiness = {
        row["dataset_name"]: row
        for row in read_json(project_root / "observability/reports/dataset_readiness.json", [])
    }
    slo_report = read_json(project_root / "observability/reports/slo_report.json", {"gold_slos": []})
    failed_slos = {row["dataset_name"]: row for row in slo_report.get("gold_slos", []) if row["slo_status"] == "failed"}
    semantic_report = read_json(project_root / "semantic_layer/reports/semantic_validation_report.json", {"status": "unknown"})
    reconciliation_report = read_json(project_root / "data_quality/reports/reconciliation_report.json", {"status": "unknown"})
    pii_report = read_json(project_root / "security/pii_scan_report.json", {"status": "unknown"})
    catalog_report = read_json(project_root / "metadata/catalog_validation_report.json", {"status": "unknown"})
    trust_report = read_json(project_root / "observability/reports/dataset_trust_scores.json", {"datasets": []})
    trust_by_dataset = {row["dataset_name"]: row for row in trust_report.get("datasets", [])}
    alerts = [alert for alert in read_jsonl(project_root / "alerts/alert_log.jsonl") if alert.get("resolution_status") == "open"]

    products = []
    for product in manifest.get("data_products", []):
        blockers: list[str] = []
        warnings: list[str] = []
        datasets = product["datasets"]
        trust_threshold = product.get("trust_score_threshold", 90 if product.get("tier") == "tier_1" else 75)

        for dataset in datasets:
            dataset_readiness = readiness.get(dataset)
            if not dataset_readiness:
                blockers.append(f"{dataset} has no readiness record")
                continue
            if dataset_readiness.get("readiness_status") != "ready":
                blockers.append(f"{dataset} readiness is {dataset_readiness.get('readiness_status')}")
            if dataset in failed_slos:
                blockers.append(f"{dataset} failed SLO target")
            trust = trust_by_dataset.get(dataset)
            if trust:
                score = trust.get("trust_score_overall", 0)
                if score < trust_threshold:
                    blockers.append(f"{dataset} trust score {score} below threshold {trust_threshold}")
                elif trust.get("trust_score_band") != "Trusted":
                    warnings.append(f"{dataset} trust band is {trust.get('trust_score_band')}")
            elif trust_by_dataset:
                blockers.append(f"{dataset} missing trust score")

        related_alerts = [
            alert
            for alert in alerts
            if alert.get("dataset_name") in datasets
            or any(dataset in alert.get("business_impact", "") for dataset in datasets)
        ]
        for alert in related_alerts:
            if alert["severity"] == "critical":
                blockers.append(f"critical alert {alert['alert_type']} on {alert['dataset_name']}")
            else:
                warnings.append(f"{alert['severity']} alert {alert['alert_type']} on {alert['dataset_name']}")

        if semantic_report.get("status") != "passed":
            blockers.append("semantic metric validation failed")
        if pii_report.get("status") != "passed":
            blockers.append("PII classification scan failed")
        if catalog_report.get("status") != "passed":
            blockers.append("catalog validation failed")
        if any(dataset in {"gold_revenue_analytics", "gold_target_vs_actual", "gold_product_performance"} for dataset in datasets):
            if reconciliation_report.get("status") != "passed":
                blockers.append("financial reconciliation failed")

        products.append(
            {
                "name": product["name"],
                "owner": product["owner"],
                "tier": product["tier"],
                "datasets": datasets,
                "status": product_status(blockers, warnings),
                "blockers": blockers,
                "warnings": warnings,
                "quality_gate": product["quality_gate"],
                "trust_score_threshold": trust_threshold,
            }
        )

    report = {
        "certified_at": datetime.now(timezone.utc).isoformat(),
        "product_count": len(products),
        "certified_count": sum(1 for product in products if product["status"] == "certified"),
        "conditional_count": sum(1 for product in products if product["status"] == "conditional"),
        "blocked_count": sum(1 for product in products if product["status"] == "blocked"),
        "status": "blocked" if any(product["status"] == "blocked" for product in products) else "passed",
        "products": products,
    }
    output_dir = project_root / "operations/certification"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data_product_certification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "data_product_certification_report.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Data Product Certification Report",
        "",
        f"Certified at: `{report['certified_at']}`",
        "",
        "| Data Product | Owner | Tier | Status | Blockers | Warnings |",
        "|---|---|---|---|---|---|",
    ]
    for product in report["products"]:
        blockers = "<br>".join(product["blockers"]) if product["blockers"] else ""
        warnings = "<br>".join(product["warnings"]) if product["warnings"] else ""
        lines.append(
            f"| {product['name']} | {product['owner']} | {product['tier']} | {product['status']} | {blockers} | {warnings} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
