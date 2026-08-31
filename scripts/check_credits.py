"""Snapshot the OpenRouter credit state of the key in OPENAI_API_KEY.

    source .env && python scripts/check_credits.py [--label before-smoke]

Prints two lines:
- account: total purchased / used / remaining credits (USD, whole account)
- key:     this key's own spend limit, usage (incl. today), and remaining
           headroom — the binding constraint when keys carry per-key limits

Run it before and after a pipeline run to measure what the run cost;
per-call costs are also logged live by request/openai.py (LLMXMR_TRACK_COST).
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

    def get(url):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["data"]

    acct = get("https://openrouter.ai/api/v1/credits")
    keyinfo = get("https://openrouter.ai/api/v1/key")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = f" [{args.label}]" if args.label else ""
    total, used = acct["total_credits"], acct["total_usage"]
    print(f"{now}{label}  account: purchased=${total:.4f}  used=${used:.4f}  remaining=${total - used:.4f}")

    limit = keyinfo.get("limit")
    k_used = keyinfo.get("usage", 0.0)
    k_daily = keyinfo.get("usage_daily", 0.0)
    if limit is None:
        print(f"{now}{label}  key({keyinfo.get('label', '?')}): limit=none  used=${k_used:.4f}  today=${k_daily:.4f}")
    else:
        remaining = keyinfo.get("limit_remaining", limit - k_used)
        print(f"{now}{label}  key({keyinfo.get('label', '?')}): limit=${limit:.2f}  "
              f"used=${k_used:.4f}  today=${k_daily:.4f}  remaining=${remaining:.4f}")


if __name__ == "__main__":
    main()
