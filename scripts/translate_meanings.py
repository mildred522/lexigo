import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.translation import MemoryTranslationCache


def main() -> None:
    cache = MemoryTranslationCache()
    print(f"translation cache ready: {len(cache.items)} entries")


if __name__ == "__main__":
    main()
