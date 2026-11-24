"""The comparison of one answer-key ballot with one run's ballot. Used by score_ballot.py."""
import bisect
import re

import names as N

PASS, FAIL, NOT_GRADED, NOT_APPLICABLE = "pass", "fail", "not_graded", "n/a"
INVENTED = "not in the key's ballot"
UNRESOLVED = "unresolved: the key does not hold the whole ballot"
FIELDS = ("number", "type", "proponent", "nominee", "order", "title", "board_recommendation")
DIRECTOR = "director_election"
ENGINE_DIRECTOR = "director_nomination"
# A key's proposal type -> the engine types such an item can be stored as. A key type absent here is not graded.
TYPES = {
    DIRECTOR: {ENGINE_DIRECTOR},
    "auditor": {"auditor_appointment"},
    "say_on_pay": {"executive_compensation"},
    "equity_plan": {"executive_compensation"},
    "charter_or_bylaw_amendment": {"governance_changes"},
    # The types a batch's readers tell apart (a suite's reading brief); their "other" is absent here, so not graded.
    "quorum_or_bylaw_approval": {"governance_changes"},
    "consent_grant": {"governance_changes"},
    "consent_restrict": {"governance_changes"},
    "recapitalization": {"governance_changes"},
    "pill_vote": {"governance_changes"},
    "new_share_class": {"governance_changes"},
}
_BOARD = ("for", "against", "none")
_NO_RECOMMENDATION = "not stated"  # the stored value for a board that takes no position, which a key writes as "none"


def _is_director(r):
    """An engine item stored as a director election. An export from before its rows carried a type holds director
    items only , so an item without a type is one."""
    return r.get("type") in (None, ENGINE_DIRECTOR)


def _proposal_number(no):
    m = re.match(r"\s*(?:proposal|item|no)?\.?\s*(\d+)", str(no or ""), flags=re.I)
    return m.group(1).lstrip("0") if m else None


def _rising(values):
    """Indexes of one longest strictly rising run of values."""
    tails, tail_at, prev = [], [], [None] * len(values)
    for i, v in enumerate(values):
        k = bisect.bisect_left(tails, v)
        if k == len(tails):
            tails.append(v); tail_at.append(i)
        else:
            tails[k] = v; tail_at[k] = i
        prev[i] = tail_at[k - 1] if k else None
    keep, i = set(), tail_at[-1] if tail_at else None
    while i is not None:
        keep.add(i); i = prev[i]
    return keep


def _match(gold_items, records):
    """({index of gold item: record}, indexes of slate items the key prints without a name)."""
    dirs = [i for i, g in enumerate(gold_items) if g["proposal_type"] == DIRECTOR]
    titles = [gold_items[i]["item_title_as_printed"] for i in dirs]
    named = [i for i in dirs if titles.count(gold_items[i]["item_title_as_printed"]) == 1]
    slate = [i for i in dirs if i not in named]
    pairs = N.join_names([N.nominee_name(gold_items[i]["item_title_as_printed"]) for i in named],
                         [N.nominee_name(r["question"]) for r in records])
    out = {named[g]: records[e] for g, e in pairs.items()}
    taken = {id(r) for r in out.values()}
    rest = [i for i, g in enumerate(gold_items) if g["proposal_type"] != DIRECTOR]
    # A person's election is never the match of a proposal: a run that numbers its items in one count gives a nominee
    # the number a proposal prints.
    left = [r for r in records if id(r) not in taken and not _is_director(r)]
    gold_keys = [N._item_key(gold_items[i]["item_no"]) for i in rest]
    run_keys = [N._item_key(r.get("qid")) for r in left]
    for i, k in zip(rest, gold_keys):
        if k and gold_keys.count(k) == 1 and run_keys.count(k) == 1:
            out[i] = left[run_keys.index(k)]
    return out, slate


def _fields(g, r):
    is_dir = g["proposal_type"] == DIRECTOR
    if is_dir:
        a, b = _proposal_number(g["item_no"]), _proposal_number(r.get("qid"))
        number = NOT_GRADED if a is None or b is None else PASS if a == b else FAIL
    else:
        number = PASS
    allowed = TYPES.get(g["proposal_type"])
    kind = NOT_GRADED if allowed is None or r.get("type") is None else PASS if r["type"] in allowed else FAIL
    stored = (r.get("row") or {}).get("isShareholderProposal")
    proponent = g.get("proponent")
    if proponent not in ("management", "shareholder") or not isinstance(stored, bool):
        who = NOT_GRADED
    else:
        who = PASS if stored == (proponent == "shareholder") else FAIL
    wanted, board = str(g.get("board_recommendation") or "").lower(), str(r.get("board") or "none").strip().lower()
    board = "none" if board == _NO_RECOMMENDATION else board
    # A frequency vote's recommendation is a number of years, which a key's for or against cannot be read against.
    recommendation = NOT_GRADED if wanted not in _BOARD or "board" not in r or "year" in board else PASS if wanted == board else FAIL
    return {"number": number, "type": kind, "proponent": who, "nominee": PASS if is_dir else NOT_APPLICABLE,
            "order": NOT_GRADED, "title": NOT_GRADED, "board_recommendation": recommendation}


def compare_meeting(gold_items, records, *, complete):
    """One meeting. gold_items: its Ballot_items rows in the key's order; records: the run's item records for it
    ; complete: the key holds every item of the ballot, not director elections only.
    Returns {"items": a row per gold item, "missing": gold items nothing matched, "unmatched_engine": engine items
    nothing matched, each with its reading}."""
    matched, slate = _match(gold_items, records)
    items = []
    for i, g in enumerate(gold_items):
        r = matched.get(i)
        base = {"meeting_id": g["meeting_id"], "item_no": g["item_no"], "title": g["item_title_as_printed"]}
        if r is None:
            fields = {f: NOT_GRADED for f in FIELDS}
            items.append({**base, "matched": False, "slate": i in slate, "engine_seq": None, "engine_qid": None, "fields": fields})
        else:
            items.append({**base, "matched": True, "slate": False, "engine_seq": r.get("seq"), "engine_qid": r.get("qid"),
                          "fields": _fields(g, r)})
    ordered = [it for it in items if it["matched"] and it["engine_seq"] is not None]
    keep = _rising([it["engine_seq"] for it in ordered])
    for n, it in enumerate(ordered):
        it["fields"]["order"] = PASS if n in keep else FAIL
    taken = {id(r) for r in matched.values()}
    # A slate printed without names cannot be told apart item by item, so the run's director items stand for it.
    spare = [r for r in records if id(r) not in taken and (complete or _is_director(r))]
    slate_count = None
    if slate:
        run_directors = [r for r in records if id(r) not in taken and _is_director(r)]
        slate_count = {"meeting_id": gold_items[slate[0]]["meeting_id"], "key": len(slate), "run": len(run_directors)}
        spare = [r for r in spare if not _is_director(r)]
    return {"items": items, "slate": slate_count,
            "missing": [{k: it[k] for k in ("meeting_id", "item_no", "title")} for it in items if not it["matched"] and not it["slate"]],
            "unmatched_engine": [{"meeting_id": gold_items[0]["meeting_id"] if gold_items else r.get("meeting"), "seq": r.get("seq"),
                                  "qid": r.get("qid"), "question": r.get("question"), "type": r.get("type"),
                                  "reading": INVENTED if complete else UNRESOLVED} for r in spare]}


def compare_run(ballot_items, records, covered, *, complete):
    """Every covered meeting of a gold. ballot_items: the gold's Ballot_items rows; records: the run's item records
    with their gold meeting set ; covered: the gold meetings the run covers.
    Returns {"summary", "items", "failures", "missing", "unmatched_engine"}."""
    meetings = []
    for g in ballot_items:
        if g["meeting_id"] in covered and g["meeting_id"] not in meetings:
            meetings.append(g["meeting_id"])
    items, missing, spare, slates = [], [], [], []
    for mid in meetings:
        one = compare_meeting([g for g in ballot_items if g["meeting_id"] == mid], [r for r in records if r.get("meeting") == mid],
                              complete=complete)
        items += one["items"]; missing += one["missing"]; spare += one["unmatched_engine"]
        if one["slate"]:
            slates.append(one["slate"])
    return {"summary": summarize(meetings, items, missing, spare, slates, complete), "items": items, "failures": failures_of(items),
            "missing": missing, "unmatched_engine": spare}


def failures_of(items):
    return [{"meeting_id": it["meeting_id"], "item_no": it["item_no"], "title": it["title"], "field": f,
             "engine_seq": it["engine_seq"], "engine_qid": it["engine_qid"]}
            for it in items for f in FIELDS if it["fields"][f] == FAIL]


def summarize(meetings, items, missing, spare, slates, complete):
    """The counts of one comparison: per field, and the items outside the match."""
    counts = {f: {"pass": 0, "fail": 0, "not_graded": 0} for f in FIELDS}
    for it in items:
        for f, v in it["fields"].items():
            if v != NOT_APPLICABLE:
                counts[f][v] += 1
    return {"meetings": len(meetings), "items": len(items), "matched": sum(1 for it in items if it["matched"]),
            "slate_items_not_graded": sum(1 for it in items if it["slate"]), "key_holds_whole_ballot": complete,
            "slates": slates, "slates_with_another_count": sum(1 for s in slates if s["key"] != s["run"]),
            "missing": len(missing), "unmatched_engine": len(spare), "fields": counts}
