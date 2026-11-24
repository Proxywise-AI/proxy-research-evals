#!/usr/bin/env python3
"""A rule batch's recommendations against its answer key, item by item.

  python3 tools/score_votes.py rules/<batch> <run_id>

Reads answer_key.csv (the expected recommendation under each rule) and runs/<run_id>/engine_votes.csv, joined on
meeting, sequence and rule. Prints how many items match, how many expected votes against the board were caught,
and every wrong or missing item. A Withhold is read as the Against the key expects on a director election.
"""
import csv
import os
import sys


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm(v):
    v = (v or "").strip().lower()
    return "against" if v == "withhold" else v


def score(batch_dir, run_id):
    key = read(os.path.join(batch_dir, "answer_key.csv"))
    run = {(r["meeting_id"], r["seq"], r["rule"]): r for r in read(os.path.join(batch_dir, "runs", run_id, "engine_votes.csv"))}
    out = {"items": len(key), "match": 0, "expected_against": 0, "against_caught": 0, "wrong_against": 0, "review": 0, "misses": []}
    for k in key:
        e = run.get((k["meeting_id"], k["seq"], k["rule"]))
        want, got = norm(k["expected"]), norm(e["engine"]) if e else "missing"
        out["match"] += want == got
        out["expected_against"] += want == "against"
        out["against_caught"] += want == "against" and got == "against"
        out["wrong_against"] += want != "against" and got == "against"
        out["review"] += got == "review"
        if want != got:
            out["misses"].append({**k, "engine": got})
    return out


if __name__ == "__main__":
    s = score(sys.argv[1], sys.argv[2])
    print(f"{s['match']} of {s['items']} items match the answer key")
    print(f"{s['against_caught']} of {s['expected_against']} expected votes against the board caught; {s['wrong_against']} wrong; {s['review']} left for review")
    for m in s["misses"]:
        print("miss", m)
