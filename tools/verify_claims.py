#!/usr/bin/env python3
"""Recomputes every figure the article quotes from the files in this repo, and fails if one differs.

  python3 tools/verify_claims.py

The figures and where each comes from are listed in CLAIMS.md.
"""
import collections
import csv
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import score_ballot  # noqa: E402
import score_votes  # noqa: E402

RUNS = {"unequal-voting-rights": "R-2026-09-25-01", "sustained-underperformance": "R-2026-10-21-01",
        "overboarding": "R-2026-09-26-01", "written-consent": "R-2026-10-12-01"}
failed = []


def read(*parts):
    with open(os.path.join(ROOT, *parts), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def claim(text, got, want):
    ok = got == want
    print(("ok    " if ok else "FAIL  ") + f"{text}: {got}" + ("" if ok else f" (the article says {want})"))
    if not ok:
        failed.append(text)


# --- what is published
meetings, items, facts, quoted = set(), collections.Counter(), 0, 0
for panel in RUNS:
    for m in read("reading", panel, "meetings.csv"):
        meetings.add(m["meeting_id"])
    per_meeting = collections.Counter(b["meeting_id"] for b in read("reading", panel, "ballot_items.csv"))
    for mid, n in per_meeting.items():
        items[mid] = max(items[mid], n)  # a meeting in two panels is counted once, at its fuller ballot
    rows = read("reading", panel, "facts.csv")
    facts += len(rows)
    quoted += sum(1 for f in rows if f["source_citation"].strip())
claim("meetings in the reading panels", len(meetings), 81)
claim("their proxy seasons", sorted({m.split("-")[1] for m in meetings}), ["2024", "2025", "2026"])
claim("ballot items", sum(items.values()), 947)
claim("facts", facts, 2059)
claim("facts that carry a quote from the filing", quoted, 1710)

# --- the ballot, field by field
summaries = {p: score_ballot.score(os.path.join(ROOT, "reading", p), r)[1] for p, r in RUNS.items()}
wc = summaries["written-consent"]
s = wc["summary"]
claim("whole-ballot panel: meetings run", s["meetings"], 27)
claim("whole-ballot panel: items in the answer key", s["items"], 439)
other_number = collections.Counter(m["meeting_id"] for m in wc["missing"])
claim("  every item accounted for (matched + slates printed without names + stored under another number)",
      s["matched"] + s["slate_items_not_graded"] + s["missing"], 439)
claim("  items under another number have an unmatched engine item at the same meeting",
      other_number == collections.Counter(u["meeting_id"] for u in wc["unmatched_engine"]), True)
claim("  proposal type right / wrong where graded", (s["fields"]["type"]["pass"], s["fields"]["type"]["fail"]), (272, 0))
claim("  nominees matched by name / not matched", (s["fields"]["nominee"]["pass"], s["fields"]["nominee"]["fail"]), (222, 0))
wrong_proponent = [f for f in wc["failures"] if f["field"] == "proponent"]
claim("  items with the wrong proponent", [(f["meeting_id"]) for f in wrong_proponent], ["T-2026-AM", "T-2026-AM"])
renumbered = [f for f in wc["failures"] if f["field"] == "number"]
claim("  items not carrying the proxy card's number", len(renumbered) + s["missing"], 112)
claim("  meetings where that happens", len({f["meeting_id"] for f in renumbered} | set(other_number)), 9)
named = [(v["summary"]["fields"]["nominee"]["pass"], v["summary"]["fields"]["nominee"]["fail"]) for v in summaries.values()]
claim("named director nominees matched across the four panels / not matched", (sum(a for a, _ in named), sum(b for _, b in named)), (800, 0))

# --- the board as of the meeting
board = read("reading", "sustained-underperformance", "runs", RUNS["sustained-underperformance"], "board_at_meeting_check.csv")
claim("nominees placed on or off the committee as the filing states", (sum(r["match"] == "yes" for r in board), len(board)), (241, 241))
changed = [r for r in board if r["changed_around_meeting"]]
claim("  of them, directors whose seat changed around the meeting", (sum(r["match"] == "yes" for r in changed), len(changed)), (20, 20))

# --- facts
verdicts = collections.Counter(r["verdict"] for r in read("reading", "overboarding", "runs", RUNS["overboarding"], "fact_verdicts.csv"))
stated = verdicts["stated"] + verdicts["contradicted"]
claim("board-seat facts the engine stated", stated, 510)
claim("  of them right", verdicts["stated"], 476)
claim("  share right, rounded", round(100 * verdicts["stated"] / stated), 93)
claim("  facts the engine said nothing on", verdicts["not stated"], 177)
in_key = stated + verdicts["not stated"]
claim("  facts in the answer key that were graded", in_key, 687)
claim("  share of them the engine stated right, rounded", round(100 * verdicts["stated"] / in_key), 69)

# --- the batch of responsiveness rules
batch = os.path.join(ROOT, "rules", "batch-responsiveness-rules")
claim("rule batch: meetings", len(read("rules", "batch-responsiveness-rules", "meetings.csv")), 28)
by_rule = collections.Counter(r["rule"] for r in read("rules", "batch-responsiveness-rules", "answer_key.csv"))
claim("rule batch: director items and say-on-pay items", (by_rule["board-responsiveness"], by_rule["say-on-pay-responsiveness"]), (244, 26))
for run in sorted(os.path.basename(p) for p in glob.glob(os.path.join(batch, "runs", "*"))):
    v = score_votes.score(batch, run)
    claim(f"rule batch, {run}: items matching the answer key", (v["match"], v["items"]), (270, 270))
    claim(f"rule batch, {run}: votes against the board caught / wrong", (v["against_caught"], v["expected_against"], v["wrong_against"]), (11, 11, 0))

print()
print("every figure checks out" if not failed else f"{len(failed)} figure(s) differ")
sys.exit(1 if failed else 0)
