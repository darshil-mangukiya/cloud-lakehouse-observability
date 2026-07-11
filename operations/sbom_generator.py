from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_requirements(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    packages = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-r "):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)(.*)", stripped)
        if match:
            packages.append({"name": match.group(1), "specifier": match.group(2) or ""})
    return packages


def parse_docker_images(compose_path: Path) -> list[str]:
    if not compose_path.exists():
        return []
    images = []
    for line in compose_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("image:"):
            images.append(stripped.split(":", 1)[1].strip())
    return images


def generate_sbom(project_root: Path) -> dict[str, Any]:
    requirements = {
        "requirements.txt": parse_requirements(project_root / "requirements.txt"),
        "requirements-airflow.txt": parse_requirements(project_root / "requirements-airflow.txt"),
        "requirements-dev.txt": parse_requirements(project_root / "requirements-dev.txt"),
    }
    docker_images = parse_docker_images(project_root / "docker-compose.yml")
    dockerfiles = sorted(str(path.relative_to(project_root)) for path in (project_root / "docker").rglob("Dockerfile"))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "package_file_count": len(requirements),
        "package_count": sum(len(packages) for packages in requirements.values()),
        "docker_image_count": len(docker_images),
        "dockerfile_count": len(dockerfiles),
        "requirements": requirements,
        "docker_images": docker_images,
        "dockerfiles": dockerfiles,
    }
    output_dir = project_root / "operations/sbom"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "software_inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "software_inventory.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Software Inventory",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        f"- Python package entries: `{report['package_count']}`",
        f"- Docker images: `{report['docker_image_count']}`",
        f"- Dockerfiles: `{report['dockerfile_count']}`",
        "",
        "## Docker Images",
        "",
    ]
    lines.extend(f"- `{image}`" for image in report["docker_images"])
    lines.extend(["", "## Python Requirements", ""])
    for file_name, packages in report["requirements"].items():
        lines.append(f"### {file_name}")
        for package in packages:
            lines.append(f"- `{package['name']}{package['specifier']}`")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
