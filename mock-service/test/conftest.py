import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["NSC_DATA_FILE"] = str(ROOT / "data" / "test_records.json")

app_pkg = types.ModuleType("app")
app_pkg.__path__ = [
    str(ROOT / "api" / "app"),
    str(ROOT / "auth" / "app"),
]
sys.modules.setdefault("app", app_pkg)

for candidate in (ROOT / "api", ROOT / "auth"):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)
