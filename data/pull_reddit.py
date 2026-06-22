"""Pull real r/television comments from the pullpush.io research archive.

pullpush.io is a free, no-auth successor to Pushshift that mirrors Reddit
content for research. We use COMMENTS (not submissions) because in r/television
the "takes" live in the comments -- submissions are mostly news headlines/links.

Usage:
    python3 pull_reddit.py --subreddit television --pages 5 --out raw_comments.json

Each page is up to 100 comments; we paginate backwards in time using the
`before` epoch cursor so we get a varied pool rather than 100 near-duplicates.
"""
import argparse
import json
import subprocess
import time
import urllib.parse

API = "https://api.pullpush.io/reddit/search/comment/"
UA = "TakeMeter-research/0.1 (course project; classification dataset)"


def fetch(subreddit, size=100, before=None):
    # Shell out to curl: portable across machines where Python lacks CA certs.
    params = {"subreddit": subreddit, "size": size, "sort": "desc", "sort_type": "created_utc"}
    if before:
        params["before"] = before
    url = API + "?" + urllib.parse.urlencode(params)
    out = subprocess.run(
        ["curl", "-s", "-A", UA, "--max-time", "40", url],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out).get("data", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subreddit", default="television")
    ap.add_argument("--pages", type=int, default=5)
    ap.add_argument("--out", default="raw_comments.json")
    args = ap.parse_args()

    seen, rows, before = set(), [], None
    for p in range(args.pages):
        batch = fetch(args.subreddit, 100, before)
        if not batch:
            break
        for c in batch:
            cid = c.get("id")
            if cid in seen:
                continue
            seen.add(cid)
            rows.append({
                "id": cid,
                "body": c.get("body", ""),
                "score": c.get("score"),
                "author": c.get("author"),
                "created_utc": c.get("created_utc"),
                "link_id": c.get("link_id"),
                "permalink": c.get("permalink"),
            })
        before = batch[-1].get("created_utc")  # paginate older
        print(f"page {p+1}: +{len(batch)} (total unique {len(rows)})")
        time.sleep(1.0)  # be polite to the free API

    with open(args.out, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"saved {len(rows)} comments -> {args.out}")


if __name__ == "__main__":
    main()
