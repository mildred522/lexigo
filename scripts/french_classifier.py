import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.models import NormalizedWord

TEMPLATE_PATTERNS = (
    re.compile(r"^Premi(?:\u00e8|e)re personne du singulier\b", re.IGNORECASE),
    re.compile(r"^(?:Deuxi(?:\u00e8|e)me|Troisi(?:\u00e8|e)me) personne\b", re.IGNORECASE),
    re.compile(r"^(F(?:\u00e9|e)minin|Masculin)(?: (singulier|pluriel))? de ", re.IGNORECASE),
    re.compile(r"^Pluriel de ", re.IGNORECASE),
    re.compile(r"^Participe (pr(?:\u00e9|e)sent|pass(?:\u00e9|e))\b", re.IGNORECASE),
    re.compile(r"^Contraction de (?:de |a |(?:l['\u2019])|(?:d['\u2019]))", re.IGNORECASE),
    re.compile(r"^(?:Nom|Lettre) de la lettre de l(?:'|\u2019)alphabet\b", re.IGNORECASE),
    re.compile(
        r"^(?:Premi(?:\u00e8|e)re|\w+(?:\u00e8|e)me) lettre "
        r"(?:de|et .+? voyelle de) l(?:'|\u2019)alphabet\b",
        re.IGNORECASE,
    ),
)


def classify_french_entry(word: NormalizedWord) -> str:
    source_text = word.meaning_source_text.strip()
    if not source_text:
        return "blocked"

    if any(pattern.search(source_text) for pattern in TEMPLATE_PATTERNS):
        return "rule_based"

    return "local_candidate"
