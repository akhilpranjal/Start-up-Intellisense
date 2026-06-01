from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipeline import embed_companies  # noqa: E402


def main() -> None:
    """Description:
Run the embedding pipeline entry point.
Input Description:
No direct inputs.
Output Description:
Prints the number of embedded companies.
"""
    count = embed_companies()
    print(f"embedded {count} companies")


if __name__ == "__main__":
    main()
