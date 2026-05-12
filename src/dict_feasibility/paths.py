from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProjectDirs:
    root: Path
    sources_dir: Path
    artifacts_dir: Path
    normalized_dir: Path
    reports_dir: Path


def ensure_project_dirs(root: Path) -> ProjectDirs:
    sources_dir = root / "sources"
    artifacts_dir = root / "artifacts"
    normalized_dir = artifacts_dir / "normalized"
    reports_dir = artifacts_dir / "reports"
    for path in (sources_dir, artifacts_dir, normalized_dir, reports_dir):
        path.mkdir(parents=True, exist_ok=True)
    return ProjectDirs(
        root=root,
        sources_dir=sources_dir,
        artifacts_dir=artifacts_dir,
        normalized_dir=normalized_dir,
        reports_dir=reports_dir,
    )
