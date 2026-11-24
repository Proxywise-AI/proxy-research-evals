# Batch responsiveness rules

A first test of the later steps of the framework: did the right rule fire, and did the recommendation follow
the rule. Two rules are tested together on one set of 28 meetings.

| Rule | Scored on | Items |
|---|---|---|
| [Board responsiveness to shareholder votes](rules/board-responsiveness.md) | every director election | 244 |
| [Say-on-pay responsiveness](rules/say-on-pay-responsiveness.md) | the say-on-pay item | 26 |

Both rules turn on last year's vote results and on how the board responded. The rules are part of a benchmark
rule set we use for testing. They are not a recommendation on how anyone should vote.

## Files

- `meetings.csv`: the 28 meetings, with last year's say-on-pay support as the answer key reads it.
- `rules/`: the rule text the two runs read.
- `answer_key.csv`: the expected recommendation on each of the 270 items (version 1.1).
- `runs/<run_id>/engine_votes.csv`: the engine's recommendation on each item, and `run.json`.

## Result

| Run | Engine | Items matching the answer key | Votes against the board caught | Wrong votes against the board |
|---|---|---|---|---|
| R-2026-11-17-02 | v0.8.135 | 270 of 270 | 11 of 11 | 0 |
| R-2026-11-20-02 | v0.8.154 | 270 of 270 | 11 of 11 | 0 |

```bash
python3 tools/score_votes.py rules/batch-responsiveness-rules R-2026-11-20-02
```

## How to read this result

**These are the 28 meetings the two rules and the engine were developed on.** Earlier runs on the same meetings
scored lower, and the rule wording, the engine and the answer key were each corrected along the way. The result
shows that the pipeline works end to end on these meetings. It is not an estimate of accuracy on meetings the
engine has not seen.

Of the 270 items, 259 are expected For and 11 Against, so a system that always answered For would match 259.
The 11 are the test: 8 director elections and 3 say-on-pay votes.
