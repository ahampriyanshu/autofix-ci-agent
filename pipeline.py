from __future__ import annotations

import json
import sys
from typing import Any, Dict

from src.orchestrator import orchestrate_ci_fix


def run(seed_name: str) -> Dict[str, Any]:
    """Run the CI autofix agent on the provided seed scenario."""
    return orchestrate_ci_fix(seed_name)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        sys.stdout.write(
            json.dumps(
                {"error": "Provide the seed scenario name as argument"},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        sys.stdout.flush()
        return 1
    seed_name = args[0]
    out = run(seed_name)
    sys.stdout.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    sys.stdout.flush()
    return 0


__all__ = ["run", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
