from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipeline import extract_companies  # noqa: E402


def main() -> None:
    """Description:
Run the extraction pipeline entry point.
Input Description:
No direct inputs.
Output Description:
Prints the number of extracted companies.
"""
    count = extract_companies()
    print(f"extracted {count} companies")


if __name__ == "__main__":
    main()
