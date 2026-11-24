# Proxy research evals

Answer keys, engine output and scoring tools for checking whether an AI system read a proxy statement correctly.
Published with the article "How do you know if AI actually read the proxy statement correctly?" (Evaluating
AI-based proxy research, part 2).

The repo covers the first two steps of our five-step evaluation framework, reading the ballot and pulling out
the facts, on 81 annual meetings of US companies from the 2024 to 2026 proxy seasons. It also holds a first test
of the later steps: two voting rules on 28 meetings.

Every figure the article quotes can be recomputed from the files here:

```bash
python3 tools/verify_claims.py
```

[CLAIMS.md](CLAIMS.md) lists each figure, the file it comes from and what it does and does not show.

## What is here

```
reading/<panel>/
  meetings.csv              the meetings, each with its SEC accession number and filing link
  ballot_items.csv          the answer key's ballot: number, title as printed, proposal type, proponent
  facts.csv                 the answer key's facts, each with its quote and section where the filing states it
  runs/<run_id>/
    run.json                engine version, model, answer-key version
    engine_ballot.csv       the ballot as our engine stored it
    ballot_fields.csv       the ballot check, a row per item and a column per field
    ballot_summary.json     its counts, and every failed, missing or unmatched item
    fact_verdicts.csv       (overboarding) each answer-key fact: stated, contradicted or not stated
    board_at_meeting_check.csv  (sustained-underperformance) each nominee's committee seat as of the meeting
rules/batch-responsiveness-rules/   two voting rules on 28 meetings: rule text, answer key, two engine runs
tools/
  score_ballot.py           the ballot, field by field
  score_votes.py            a rule batch's recommendations against its answer key
  verify_claims.py          recomputes the article's figures
```

## The four reading panels

Each panel was built to test one hard reading problem, so the meetings are picked for difficulty. They are not
a market sample, and nothing here is an overall accuracy rate.

| Panel | Meetings | Ballot items | Facts | What the facts cover |
|---|---|---|---|---|
| `unequal-voting-rights` | 11 | 114 director elections | 205 | share classes, votes per share, controlling holders, the nominating committee |
| `sustained-underperformance` | 23 | 241 director elections | 700 | shareholder return figures, governance provisions, the nominating committee as of the meeting |
| `overboarding` | 27 | 223 director elections | 868 | each nominee's other public company boards and CEO roles |
| `written-consent` | 28 (27 run) | 461, the whole ballot | 286 | special-meeting rights, voting standard, written consent and related provisions |

Some meetings sit in more than one panel: 81 different meetings and 947 different ballot items in all.

The facts are what a filing states or what follows from it by arithmetic. No voting policy is applied in these
panels: there are no recommendations, no rule outcomes and no other provider's recommendations in the files.

## Reading conventions

- **Sources.** Tier 1 is the meeting's definitive proxy statement. Tier 2 is another SEC filing or the company's
  charter or bylaws. Nothing else is used for an answer key. `source_tier` says which.
- **Quotes.** A fact read from a filing carries the section and the exact quote in `source_citation`. A fact that
  records an absence ("no other public boards", "not a sitting CEO") or a figure computed from other facts
  has no quote: 1,710 of the 2,059 facts carry one.
- **Dates.** Board and committee seats are read as of the meeting date: the proxy's roster plus any change a
  filing says takes effect by then.
- **Ballot numbers.** An item carries the number printed on the proxy card. Where a card prints one number for
  several nominees, the key numbers them apart (1.01, 1.02 or 1a, 1b).
- **Proponent.** `management` or `shareholder`, as the proxy states.

## How the answer keys were built

Every answer key is built from the filings only, without looking at our engine's output.

- **Reading panels (September and October 2026).** One AI reader per filing recorded each fact with its quote.
  A second model then checked the claims against the filing, and a person read the flagged claims and the rows
  that decide an outcome. `reviewed_by_a_person` in `facts.csv` says which facts a person checked: 581 of 2,059.
  The rest are AI-drafted and may contain errors.
- **Rule batch (November 2026).** Three AI readers from two providers read each filing independently. Code
  checked that every quote appears in the filing. Disagreements and deciding judgments went to people.

An answer key is frozen with a version number, and a correction is a new version. If you think a row is wrong,
open an issue naming the meeting, the item and the filing passage.

## Scoring

```bash
python3 tools/score_ballot.py reading/written-consent R-2026-10-12-01
python3 tools/score_votes.py rules/batch-responsiveness-rules R-2026-11-20-02
```

- **The ballot** is checked field by field: number, proposal type, proponent, nominee and order. Items are
  matched one to one and never by position. Titles are not graded by this tool, because a stored title is a
  short restatement and comparing it is a judgment of meaning.
- **The facts** are graded one by one as stated, contradicted or not stated in the engine's stored output. That
  grading is done by a model with a control per check, so the verdicts are published as data
  (`fact_verdicts.csv`), not recomputed here.
- **To score your own system**, write its ballot in the format of `engine_ballot.csv` into a new run folder with
  a `run.json`, and run `score_ballot.py` on it.

The tools need Python 3.9 or later and no packages.

## What to keep in mind

- The engine runs are dated and versioned. The reading runs are from September and October 2026; the engine has
  changed since, including how it numbers ballot items.
- The rule batch reports the meetings the rules and the engine were developed on. See its README.
- "Answer key" in the text is called "gold" in parts of the code.

## License

Data: CC BY 4.0. Code: MIT. See [LICENSE.md](LICENSE.md).
