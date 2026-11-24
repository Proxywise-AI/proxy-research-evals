#!/usr/bin/env python3
"""The ballot, field by field: one run's ballot against a panel's answer key.

  python3 tools/score_ballot.py reading/<panel> <run_id>

Reads reading/<panel>/ballot_items.csv (the answer key) and runs/<run_id>/engine_ballot.csv (what the engine
stored), and writes ballot_fields.csv (a row per answer-key item, a column per field) and ballot_summary.json
into the run folder.

Items are matched one to one and never by position, so a wrong field cannot hide behind a pairing:
  a director election   by the nominee's name, against every engine item whatever its type;
  any other item        by its printed number, when exactly one unmatched item on each side carries it.
An answer-key item nothing matched is missing. Where the key holds the whole ballot, an engine item nothing
matched is "not in the key's ballot". A missing item and an unmatched engine item at one meeting can be one
item stored under another number.

The fields, each pass, fail or not graded:
  number      a director election: the proposal's own number. Any other item was matched on its number.
  type        the key's proposal type against the types the engine can store it as.
  proponent   management or shareholder; not graded where the run's export has no such flag.
  nominee     the nominee matched by name.
  order       matched items must rise in the engine's sequence in the key's order.
  title       not graded here: a stored title is a short restatement, so comparing it is a judgment of meaning.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ballot_core as core  # noqa: E402


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score(panel_dir, run_id):
    run_dir = os.path.join(panel_dir, "runs", run_id)
    with open(os.path.join(run_dir, "run.json")) as f:
        run = json.load(f)
    key = read(os.path.join(panel_dir, "ballot_items.csv"))
    records = [{"meeting": r["meeting_id"], "seq": int(r["seq"]) if r["seq"] else None, "qid": r["number"] or None, "question": r["title"],
                "type": r["type"] or None, "row": {"isShareholderProposal": {"yes": True, "no": False}.get(r["shareholder_proposal"])}}
               for r in read(os.path.join(run_dir, "engine_ballot.csv"))]
    covered = {m["meeting_id"] for m in read(os.path.join(panel_dir, "meetings.csv")) if m["in_run"] == "yes"}
    return run_dir, core.compare_run(key, records, covered, complete=run["key_holds_whole_ballot"])


def main():
    panel_dir, run_id = sys.argv[1], sys.argv[2]
    run_dir, out = score(panel_dir, run_id)
    fields = [f for f in core.FIELDS if f != "board_recommendation"]
    with open(os.path.join(run_dir, "ballot_fields.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["meeting_id", "item_no", "matched", "engine_seq", "engine_number", *fields])
        w.writeheader()
        for it in out["items"]:
            w.writerow({"meeting_id": it["meeting_id"], "item_no": it["item_no"], "matched": "yes" if it["matched"] else "no",
                        "engine_seq": "" if it["engine_seq"] is None else it["engine_seq"], "engine_number": it["engine_qid"] or "",
                        **{k: it["fields"][k] for k in fields}})
    summary = out["summary"]
    summary["fields"].pop("board_recommendation", None)
    with open(os.path.join(run_dir, "ballot_summary.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "failures": out["failures"], "missing": out["missing"], "unmatched_engine": out["unmatched_engine"]},
                  f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
