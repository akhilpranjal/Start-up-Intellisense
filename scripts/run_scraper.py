"""Small CLI to run YC Playwright scraper for demo purposes."""
import sys
from pathlib import Path

# Allow `python scripts/run_scraper.py ...` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scrapers.yc_playwright import scrape_yc_companies


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/run_scraper.py yc [max_pages]")
        raise SystemExit(1)

    typ = sys.argv[1]
    if typ == "yc":
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        out = scrape_yc_companies(max_pages=max_pages)
        print(out)
    else:
        print("unknown type; use: yc")


if __name__ == "__main__":
    main()
