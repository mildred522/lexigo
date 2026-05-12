import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class SourceSpec:
    key: str
    source_name: str
    download_url: str
    version: str
    license_name: str
    notes: str


@dataclass(slots=True)
class SourceRegistry:
    specs: list[SourceSpec]

    def write(self, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(spec) for spec in self.specs]
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
