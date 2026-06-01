from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipeline import scrape_yc_once  # noqa: E402


def main() -> None:
    """Description:
Run the YC scraping pipeline entry point.
Input Description:
No direct inputs.
Output Description:
Prints the number of scraped companies.
"""
    count = scrape_yc_once()
    print(f"scraped {count} companies")


if __name__ == "__main__":
    main()
