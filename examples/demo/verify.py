from __future__ import annotations

from pathlib import Path


def main() -> int:
    result = Path("demo-result.txt")
    if not result.exists():
        print("demo-result.txt is missing")
        return 1
    if result.read_text(encoding="utf-8") != "verified\n":
        print("demo-result.txt did not contain the verified value")
        return 1
    print("verified demo-result.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
