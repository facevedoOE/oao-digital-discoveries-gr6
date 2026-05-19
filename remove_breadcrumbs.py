"""Strip the breadcrumb <nav> block (and its HTML comment) from every page.

Targets the block that looks like:

    <!-- ========== BREADCRUMB ========== -->
    <nav class="breadcrumb-bar">
      ...
    </nav>

Leaves the CSS rules in <style> intact (unused but harmless).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Match the comment (optional) + the nav block + any trailing blank line.
PATTERN = re.compile(
    r"(?:[ \t]*<!--\s*=*\s*BREADCRUMB\s*=*\s*-->\s*\n)?"
    r"[ \t]*<nav class=\"breadcrumb-bar\">.*?</nav>\s*\n",
    re.DOTALL,
)


def strip_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text, count = PATTERN.subn("", text, count=1)
    if count and new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    targets = sorted(ROOT.glob("Unit*/*.html"))
    changed = []
    skipped = []
    for f in targets:
        if "breadcrumb-bar" not in f.read_text(encoding="utf-8"):
            continue
        if strip_file(f):
            changed.append(f)
        else:
            skipped.append(f)
    print(f"Changed: {len(changed)} file(s)")
    for f in changed:
        print(f"  - {f.relative_to(ROOT)}")
    if skipped:
        print(f"Skipped (pattern not matched): {len(skipped)}")
        for f in skipped:
            print(f"  - {f.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
