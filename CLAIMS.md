# The article's figures and where they come from

`python3 tools/verify_claims.py` recomputes each figure below and fails if one differs.

| The article says | Figure | Comes from |
|---|---|---|
| Meetings published for ballots and facts | 81, from the 2024 to 2026 proxy seasons | `reading/*/meetings.csv` |
| Ballot items | 947 | `reading/*/ballot_items.csv`; a meeting in two panels counted once |
| Facts | 2,059, of which 1,710 carry a quote from the filing | `reading/*/facts.csv` |
| Every item found on a 27-meeting panel | 439 of 439 | `reading/written-consent`, run R-2026-10-12-01 |
| Two shareholder proposals stored as management proposals | 2, both at AT&T's 2026 meeting | the same run's `ballot_summary.json` |
| Proposal type right wherever graded | 272 of 272 | the same |
| Items not carrying the proxy card's number | 112, at 9 meetings | the same: 68 nominees under another proposal number, 44 other items under a running number |
| Named director nominees matched | 800 of 800 | all four panels' `ballot_summary.json` |
| Directors whose seat changed around the meeting, placed correctly | 20 of 20 (all nominees: 241 of 241) | `reading/sustained-underperformance`, `board_at_meeting_check.csv` |
| Board-seat facts the engine stated, and how many were right | 476 of 510 (93%) | `reading/overboarding`, `fact_verdicts.csv` |
| Board-seat facts the engine said nothing on | 177 | the same |
| Board-seat facts in the answer key the engine stated right | 476 of 687 (69%) | the same |
| Batch responsiveness rules | 270 of 270 on 28 meetings, in two runs | `rules/batch-responsiveness-rules` |

## What the figures do not show

- **Not a market sample.** The meetings were picked for hard cases. None of these figures is an overall
  accuracy rate.
- **"Found" on the 27-meeting panel** means each answer-key item has its counterpart in the engine's ballot:
  318 matched one to one, 77 nominees on slates the key prints without names (the counts agree at all seven
  meetings), and 44 items stored under a running number where the same meeting has the same number of engine
  items left over. The last group is matched by count, not item by item.
- **Proposal type and proponent** are graded only where the answer key and the run both carry the field: 272 and
  318 of the 439 items.
- **Board-seat facts** cover three facts per nominee (other public boards, total public boards, sitting public
  CEO) on a run of September 2026, graded again in November 2026 against version 1.0 of the answer key. One
  check could not be graded.
- **The rule batch** reports the meetings the rules and the engine were developed on.

## Figures in the article that this repo does not hold

- The committee-seats test (426 of 426 seats across 27 filings) is published separately at
  https://github.com/Proxywise-AI/def14a-committee-rosters.
- The count of engine issues that started with facts (12 of 27 by mid-October 2026) comes from our issue
  tracker, which is not public.
