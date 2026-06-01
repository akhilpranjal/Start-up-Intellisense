from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.pipeline import cluster_trends  # noqa: E402


def main() -> None:
    """Description:
Run the clustering pipeline entry point.
Input Description:
No direct inputs.
Output Description:
Prints the cluster summary dictionary.
"""
    settings = get_settings()
    result = cluster_trends(min_cluster_size=settings.cluster_min_size)
    print(result)


if __name__ == "__main__":
    main()
