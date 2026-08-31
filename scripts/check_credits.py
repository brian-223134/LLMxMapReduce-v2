"""Snapshot the OpenRouter credit balance of the key in OPENAI_API_KEY.

    source .env && python scripts/check_credits.py [--label before-smoke]

Prints total purchased / used / remaining credits (USD). Run it before and
after a pipeline run to measure what the run cost; per-call costs are also
logged live by request/openai.py (LLMXMR_TRACK_COST).
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="", help="tag printed with the snapshot")
    args = parser.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY not set (source .env first)")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)["data"]

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total, used = data["total_credits"], data["total_usage"]
    label = f" [{args.label}]" if args.label else ""
    print(f"{now}{label}  purchased=${total:.4f}  used=${used:.4f}  remaining=${total - used:.4f}")


if __name__ == "__main__":
    main()
