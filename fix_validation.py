from pathlib import Path
import re

path = Path("orchestrator.py")
source = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"(?P<left>\b(?:r_[a-zA-Z0-9_]+|r.[a-zA-Z0-9_]+))"
    r"(\s+IS DISTINCT FROM\s+)"
    r"(?P<right>\b(?:c_[a-zA-Z0-9_]+|c.[a-zA-Z0-9_]+))",
    re.IGNORECASE,
)

updated, count = pattern.subn(
    lambda m: (
        f"COALESCE({m.group('left')}, 0)"
        f"{m.group(2)}"
        f"COALESCE({m.group('right')}, 0)"
    ),
    source,
)

if count != 18:
    raise SystemExit(
        f"Expected to fix 18 validation comparisons, "
        f"but found {count}. No changes saved."
    )

path.write_text(updated, encoding="utf-8")
print(f"Updated {count} validation comparisons in {path}.")
