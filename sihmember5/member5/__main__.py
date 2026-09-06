"""Command-line entry point for standalone Member 5 guidance."""

from __future__ import annotations

import argparse
import json

from .guidance import guide


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run IP-SAKTI Member 5 international IP guidance."
    )
    parser.add_argument("query", help="International IP question")
    parser.add_argument("--language", choices=("en", "hi"), default="en")
    parser.add_argument(
        "--jurisdiction", choices=("International", "India"), default="International"
    )
    args = parser.parse_args()
    print(
        json.dumps(
            guide(
                args.query,
                language=args.language,
                jurisdiction=args.jurisdiction,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

