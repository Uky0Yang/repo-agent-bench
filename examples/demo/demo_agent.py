from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    mode = sys.argv[1]
    prompt = sys.argv[2]
    value = "verified\n" if mode == "verified" else "draft\n"
    Path("demo-result.txt").write_text(value, encoding="utf-8")
    print(
        json.dumps(
            {
                "type": "result",
                "usage": {
                    "input_tokens": len(prompt.split()) + 10,
                    "output_tokens": 4,
                    "cached_input_tokens": 0,
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
