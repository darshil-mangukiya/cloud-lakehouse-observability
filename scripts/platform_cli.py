from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def command_status(_: argparse.Namespace) -> None:
    summary = read_json(PROJECT_ROOT / "observability/reports/pipeline_run_summary.json", {})
    readiness = read_json(PROJECT_ROOT / "observability/reports/dataset_readiness.json", [])
    ready = sum(1 for record in readiness if record.get("readiness_status") == "ready")
    print(f"Batch: {summary.get('batch_id', 'unknown')}")
    print(f"Quality: {summary.get('quality_status', 'unknown')}")
    print(f"Gold ready: {ready}/{len(readiness)}")
    print(f"Alerts: {summary.get('alerts_emitted', 0)}")
    print(f"Failed SLOs: {summary.get('failed_slo_count', 0)}")


def command_alerts(args: argparse.Namespace) -> None:
    alerts = read_jsonl(PROJECT_ROOT / "alerts/alert_log.jsonl")
    if args.open_only:
        alerts = [alert for alert in alerts if alert.get("resolution_status") == "open"]
    for alert in alerts:
        print(f"{alert['severity'].upper()} {alert['alert_type']} {alert['dataset_name']} :: {alert['recommended_action']}")


def command_slos(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "observability/reports/slo_report.json", {})
    print(f"Failed SLOs: {report.get('failed_slo_count', 0)}")
    for row in report.get("gold_slos", []):
        print(f"{row['slo_status'].upper()} {row['dataset_name']} score={row['readiness_score']} target={row['readiness_target']}")


def command_lineage(_: argparse.Namespace) -> None:
    events = read_jsonl(PROJECT_ROOT / "lineage/events.jsonl")
    for event in events:
        outputs = ", ".join(output["name"] for output in event.get("outputs", []))
        print(f"{event['eventType']} {event['job']['name']} -> {outputs}")


def command_catalog(_: argparse.Namespace) -> None:
    catalog = read_json(PROJECT_ROOT / "metadata/data_catalog.json", [])
    for entry in catalog:
        status = entry.get("readiness_status", "unknown")
        print(f"{entry['dataset_name']} [{entry['criticality_tier']}] owner={entry['owner']} status={status}")


def command_cost(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "observability/reports/finops/storage_cost_report.json", {})
    print(f"Total files: {report.get('total_files', 0)}")
    print(f"Total size MB: {report.get('total_size_mb', 0)}")
    print(f"Estimated monthly storage cost: ${report.get('estimated_s3_standard_monthly_cost_usd', 0)}")
    for layer in report.get("layers", []):
        print(f"{layer['layer']}: {layer['file_count']} files, {layer['size_mb']} MB")


def command_products(_: argparse.Namespace) -> None:
    manifest = read_json(PROJECT_ROOT / "metadata/data_products/data_product_manifest.json", {"data_products": []})
    for product in manifest.get("data_products", []):
        datasets = ", ".join(product["datasets"])
        print(f"{product['name']} [{product['tier']}] owner={product['owner']} status={product['certification_status']} datasets={datasets}")


def command_semantic(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "semantic_layer/reports/semantic_validation_report.json", {})
    print(f"Semantic validation: {report.get('status', 'unknown')}")
    for metric in report.get("metrics", []):
        print(f"{metric['status'].upper()} {metric['metric']} -> {metric['dataset']}")


def command_backfill(_: argparse.Namespace) -> None:
    manifest = read_json(PROJECT_ROOT / "operations/replay/backfill_manifest.json", {})
    print(f"Backfill candidates: {manifest.get('candidate_count', 0)}")
    for item in manifest.get("candidates", [])[:10]:
        print(f"{item['source_system']} {item['ingest_date']} {item['batch_id']} :: {item['bronze_file']}")


def command_reconcile(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "data_quality/reports/reconciliation_report.json", {})
    print(f"Reconciliation: {report.get('status', 'unknown')}")
    for check in report.get("checks", []):
        print(f"{check['status'].upper()} {check['check_name']} diff={check['difference']}")


def command_audit(_: argparse.Namespace) -> None:
    manifest = read_json(PROJECT_ROOT / "metadata/audit_manifest.json", {})
    print(f"Audit artifacts: {manifest.get('artifact_count', 0)}")
    print(f"Total bytes: {manifest.get('total_size_bytes', 0)}")
    for artifact in manifest.get("artifacts", [])[:10]:
        print(f"{artifact['path']} rows={artifact['row_count']} sha256={artifact['sha256'][:12]}")


def command_pii(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "security/pii_scan_report.json", {})
    print(f"PII scan: {report.get('status', 'unknown')}")
    for dataset in report.get("datasets", []):
        if dataset.get("detected_pii_columns"):
            columns = ", ".join(dataset["detected_pii_columns"])
            print(f"{dataset['status'].upper()} {dataset['dataset_name']} pii={columns}")


def command_catalog_check(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "metadata/catalog_validation_report.json", {})
    print(f"Catalog validation: {report.get('status', 'unknown')}")
    print(f"Catalog entries: {report.get('catalog_entry_count', 0)}")
    if report.get("missing_gold_catalog_entries"):
        print("Missing gold catalog entries: " + ", ".join(report["missing_gold_catalog_entries"]))


def command_graph(_: argparse.Namespace) -> None:
    graph = read_json(PROJECT_ROOT / "lineage/lineage_graph.json", {})
    print(f"Lineage graph nodes: {graph.get('node_count', 0)}")
    print(f"Lineage graph edges: {graph.get('edge_count', 0)}")
    for edge in graph.get("edges", [])[:12]:
        print(f"{edge['source']} -> {edge['target']}")


def command_runtime(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "observability/reports/runtime/runtime_profile.json", {})
    print(f"Pipeline duration seconds: {report.get('total_duration_seconds', 0)}")
    for step in report.get("steps", []):
        print(f"{step['step_name']}: {step['duration_seconds']}s")


def command_certify(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/certification/data_product_certification_report.json", {})
    print(f"Certification status: {report.get('status', 'unknown')}")
    for product in report.get("products", []):
        print(f"{product['status'].upper()} {product['name']} blockers={len(product['blockers'])}")


def command_release(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/release/release_gate_report.json", {})
    print(f"Release status: {report.get('release_status', 'unknown')}")
    print(f"Publish decision: {report.get('publish_decision', 'unknown')}")
    for gate in report.get("gates", []):
        if gate["status"] != "passed":
            print(f"{gate['status'].upper()} {gate['gate_name']} severity={gate['severity']} observed={gate['observed']}")


def command_scorecard(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "observability/reports/scorecards/platform_trust_scorecard.json", {})
    print(f"Trust score: {report.get('trust_score', 0)}")
    print(f"Trust status: {report.get('trust_status', 'unknown')}")
    for component in report.get("components", []):
        print(f"{component['name']}: {component['score']} weight={component['weight']}")


def command_exceptions(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/exceptions/exception_evaluation_report.json", {})
    print(f"Exception status: {report.get('status', 'unknown')}")
    print(f"Active exceptions: {report.get('active_exception_count', 0)}")
    for gate in report.get("gates", []):
        if gate.get("exception_applied"):
            print(f"EXCEPTION {gate['gate_name']} ids={','.join(gate['exception_ids'])}")


def command_remediate(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/remediation/remediation_plan.json", {})
    print(f"Remediation tasks: {report.get('task_count', 0)}")
    print(f"P1 tasks: {report.get('p1_count', 0)}")
    for task in report.get("tasks", [])[:12]:
        print(f"{task['task_id']} {task['priority']} {task['owner']} {task['gate_name']} :: {task['recommended_action']}")


def command_coverage(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "metadata/control_coverage/control_coverage_report.json", {})
    print(f"Control coverage: {report.get('control_coverage_pct', 0)}")
    print(f"Sources: {report.get('source_count', 0)}")
    print(f"Gold datasets: {report.get('gold_dataset_count', 0)}")


def command_scenarios(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/scenarios/scenario_catalog.json", {})
    print(f"Scenarios: {report.get('scenario_count', 0)}")
    for scenario in report.get("scenarios", []):
        print(f"{scenario['scenario_id']} {scenario['name']} -> {', '.join(scenario['expected_detection'])}")


def command_handoff(_: argparse.Namespace) -> None:
    path = PROJECT_ROOT / "docs/FINAL_PROJECT_HANDOFF.md"
    print(str(path))
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[:20]:
            print(line)


def command_doctor(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/preflight/preflight_report.json", {})
    print(f"Preflight status: {report.get('status', 'unknown')}")
    print(f"Failed checks: {report.get('failed_count', 0)}")
    print(f"Warnings: {report.get('warning_count', 0)}")
    for check in report.get("checks", []):
        if check["status"] != "passed":
            print(f"{check['status'].upper()} {check['name']} :: {check['details']}")


def command_inventory(_: argparse.Namespace) -> None:
    report = read_json(PROJECT_ROOT / "operations/sbom/software_inventory.json", {})
    print(f"Package entries: {report.get('package_count', 0)}")
    print(f"Docker images: {report.get('docker_image_count', 0)}")
    print(f"Dockerfiles: {report.get('dockerfile_count', 0)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the local lakehouse platform.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    status = subcommands.add_parser("status", help="Show latest pipeline status.")
    status.set_defaults(func=command_status)

    alerts = subcommands.add_parser("alerts", help="Show alert log.")
    alerts.add_argument("--open-only", action="store_true")
    alerts.set_defaults(func=command_alerts)

    slos = subcommands.add_parser("slos", help="Show SLO status.")
    slos.set_defaults(func=command_slos)

    lineage = subcommands.add_parser("lineage", help="Show lineage events.")
    lineage.set_defaults(func=command_lineage)

    catalog = subcommands.add_parser("catalog", help="Show catalog entries.")
    catalog.set_defaults(func=command_catalog)

    cost = subcommands.add_parser("cost", help="Show storage usage and cost estimate.")
    cost.set_defaults(func=command_cost)

    products = subcommands.add_parser("products", help="Show data product manifest.")
    products.set_defaults(func=command_products)

    semantic = subcommands.add_parser("semantic", help="Show semantic metric validation.")
    semantic.set_defaults(func=command_semantic)

    backfill = subcommands.add_parser("backfill", help="Show bronze replay candidates.")
    backfill.set_defaults(func=command_backfill)

    reconcile = subcommands.add_parser("reconcile", help="Show silver-to-gold reconciliation status.")
    reconcile.set_defaults(func=command_reconcile)

    audit = subcommands.add_parser("audit", help="Show artifact audit manifest.")
    audit.set_defaults(func=command_audit)

    pii = subcommands.add_parser("pii", help="Show PII classification scan.")
    pii.set_defaults(func=command_pii)

    catalog_check = subcommands.add_parser("catalog-check", help="Show catalog completeness validation.")
    catalog_check.set_defaults(func=command_catalog_check)

    graph = subcommands.add_parser("graph", help="Show generated lineage graph summary.")
    graph.set_defaults(func=command_graph)

    runtime = subcommands.add_parser("runtime", help="Show pipeline runtime profile.")
    runtime.set_defaults(func=command_runtime)

    certify = subcommands.add_parser("certify", help="Show data product certification report.")
    certify.set_defaults(func=command_certify)

    release = subcommands.add_parser("release", help="Show release gate decision.")
    release.set_defaults(func=command_release)

    scorecard = subcommands.add_parser("scorecard", help="Show platform trust scorecard.")
    scorecard.set_defaults(func=command_scorecard)

    exceptions = subcommands.add_parser("exceptions", help="Show release exception evaluation.")
    exceptions.set_defaults(func=command_exceptions)

    remediate = subcommands.add_parser("remediate", help="Show generated remediation plan.")
    remediate.set_defaults(func=command_remediate)

    coverage = subcommands.add_parser("coverage", help="Show control coverage report.")
    coverage.set_defaults(func=command_coverage)

    scenarios = subcommands.add_parser("scenarios", help="Show production scenario catalog.")
    scenarios.set_defaults(func=command_scenarios)

    handoff = subcommands.add_parser("handoff", help="Show final project handoff path and preview.")
    handoff.set_defaults(func=command_handoff)

    doctor = subcommands.add_parser("doctor", help="Show local preflight report.")
    doctor.set_defaults(func=command_doctor)

    inventory = subcommands.add_parser("inventory", help="Show software inventory.")
    inventory.set_defaults(func=command_inventory)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
