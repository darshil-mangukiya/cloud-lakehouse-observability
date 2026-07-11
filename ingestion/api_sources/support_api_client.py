from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MOCK_API_PAGES = {
    None: {
        "request_id": "req_support_page_1",
        "next_page_token": "page_2",
        "tickets": [
            {"ticket_id": "api_t_001", "customer_id": "c001", "created_ts": "2026-05-11T09:15:00Z", "priority": "high", "status": "open", "topic": "billing"},
            {"ticket_id": "api_t_002", "customer_id": "c002", "created_ts": "2026-05-11T09:22:00Z", "priority": "medium", "status": "closed", "topic": "checkout"},
        ],
    },
    "page_2": {
        "request_id": "req_support_page_2",
        "next_page_token": None,
        "tickets": [
            {"ticket_id": "api_t_003", "customer_id": "c003", "created_ts": "2026-05-11T09:45:00Z", "priority": "urgent", "status": "open", "topic": "refund"},
            {"ticket_id": "", "customer_id": "c004", "created_ts": "2026-05-11T09:50:00Z", "priority": "low", "status": "open", "topic": "invalid"},
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch_mock_page(page_token: str | None) -> dict[str, Any]:
    if page_token not in MOCK_API_PAGES:
        raise ValueError(f"Unknown mock API page token: {page_token}")
    return MOCK_API_PAGES[page_token]


def validate_ticket(ticket: dict[str, Any]) -> tuple[bool, str]:
    for field in ["ticket_id", "customer_id", "created_ts"]:
        if not str(ticket.get(field, "")).strip():
            return False, f"missing required field {field}"
    if str(ticket.get("priority", "")).lower() not in {"low", "medium", "high", "urgent"}:
        return False, "invalid priority"
    return True, ""


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def ingest_support_api(project_root: Path, batch_id: str | None = None) -> dict[str, Any]:
    current_batch_id = batch_id or str(uuid.uuid4())
    page_token: str | None = None
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []

    while True:
        response = fetch_mock_page(page_token)
        request_metadata = {
            "request_id": response["request_id"],
            "page_token": page_token,
            "ingested_at": utc_now(),
            "record_count": len(response.get("tickets", [])),
        }
        requests.append(request_metadata)
        for ticket in response.get("tickets", []):
            valid, reason = validate_ticket(ticket)
            enriched = {
                **ticket,
                "_api_request_id": response["request_id"],
                "_ingest_batch_id": current_batch_id,
                "_source_system": "support_api",
                "_ingested_at": utc_now(),
            }
            if valid:
                accepted.append(enriched)
            else:
                rejected.append({**enriched, "_reject_reason": reason})
        page_token = response.get("next_page_token")
        if not page_token:
            break

    bronze_path = (
        project_root
        / "raw_data/bronze/source_system=support_api"
        / f"load_date={load_date()}"
        / f"batch_id={current_batch_id}"
        / "support_api_tickets.jsonl"
    )
    write_jsonl(bronze_path, accepted)
    rejected_path = project_root / "data_quality/reports/failed_records/support_api_rejected.jsonl"
    if rejected:
        write_jsonl(rejected_path, rejected)

    return {
        "batch_id": current_batch_id,
        "source_system": "support_api",
        "request_count": len(requests),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "bronze_path": str(bronze_path.relative_to(project_root)),
        "rejected_path": str(rejected_path.relative_to(project_root)) if rejected else None,
        "requests": requests,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run simulated support API ingestion.")
    parser.add_argument("--project-root", default=".", help="Project root path.")
    args = parser.parse_args()
    summary = ingest_support_api(Path(args.project_root).resolve())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

