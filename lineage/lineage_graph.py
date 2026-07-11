from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def generate_lineage_graph(project_root: Path) -> dict[str, Any]:
    events = read_events(project_root / "lineage/events.jsonl")
    nodes: dict[str, dict[str, str]] = {}
    edges: set[tuple[str, str, str]] = set()

    for event in events:
        job_name = event["job"]["name"]
        nodes[job_name] = {"id": job_name, "type": "job"}
        inputs = [item["name"] for item in event.get("inputs", [])]
        outputs = [item["name"] for item in event.get("outputs", [])]
        for input_name in inputs:
            nodes[input_name] = {"id": input_name, "type": "dataset"}
            edges.add((input_name, job_name, "input_to_job"))
        for output_name in outputs:
            nodes[output_name] = {"id": output_name, "type": "dataset"}
            edges.add((job_name, output_name, "job_to_output"))

    graph = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": [
            {"source": source, "target": target, "relationship": relationship}
            for source, target, relationship in sorted(edges)
        ],
    }
    graph_path = project_root / "lineage/lineage_graph.json"
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    write_mermaid(project_root / "lineage/lineage_graph.md", graph)
    return graph


def node_id(value: str) -> str:
    return "n_" + "".join(character if character.isalnum() else "_" for character in value)


def write_mermaid(path: Path, graph: dict[str, Any]) -> None:
    lines = ["# Lineage Graph", "", "```mermaid", "flowchart LR"]
    for node in graph["nodes"]:
        label = node["id"].replace('"', "'")
        shape = f'["{label}"]' if node["type"] == "dataset" else f'("{label}")'
        lines.append(f"  {node_id(node['id'])}{shape}")
    for edge in graph["edges"]:
        lines.append(f"  {node_id(edge['source'])} --> {node_id(edge['target'])}")
    lines.extend(["```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
