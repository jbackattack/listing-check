# Listing validation prototype

A small prototype that checks whether a listing shows the right information on each site, using the MLS record as the source of truth.

**This is a prototype on made-up data.** The listings, addresses and site displays are invented. It does not use real MLS data and it is not a production system.

## What it does
- Reads an MLS-style record for each listing.
- Reads what each site shows (agent platform, brand site, two portals).
- Compares status, price, address, beds, baths, square footage and description.
- Ignores formatting differences ("$725,000" vs "725000", "Lane" vs "Ln", "For Sale" vs "Active").
- Checks the seller's instructions: hidden address, and which sites may show the listing.
- Ranks each mismatch by business impact (critical, high, medium, low).
- Marks a mismatch as "recheck" if the MLS changed in the last 15 minutes, since a site may not have synced yet.
- Writes a report, a CSV of findings, and an audit log of what was checked.

It only flags. It never changes a listing. A person reviews the exceptions.

## Demo page
`docs/index.html` is a single-page version of the same checks that runs in a browser. Open it in any browser, pick a listing, and edit a site value to watch the check respond. No server or install needed.

## Run it
```
python3 listing_validator.py
python3 test_validator.py
```
Output goes to `output/` (report.md, findings.csv, audit_log.jsonl). A saved example is in `sample_output/`.

## How it handles bad input
- A missing or unreadable value in the MLS record is flagged once and skipped. The rest of that listing is still checked.
- A missing or unreadable value on a site is flagged. It does not crash the run.
- One broken record is recorded as an error and the run continues. Nothing is dropped silently.
- 12 tests cover price formats, status synonyms, hidden address leaks, syndication rules, missing listings, sync lag, truncated text and bad records.

## Why plain rules and not an LLM
Exact fields like price and status are checked with rules, so the result is the same every time and easy to audit. An LLM is a better fit for the fuzzy parts, such as mapping an unfamiliar field name, comparing description text, or explaining a mismatch in plain language. This version does not call an LLM.

## What it does not do yet
- Pull from a real feed. The next step would be reading the MLS record through the RESO Web API, after Legal confirms the data licensing terms.
- Read live pages or site APIs. Today the site displays are a file.
- Check photos, open houses or fields that differ by MLS rule set.
- Run on a schedule, send alerts, or track error rates and hours saved.
- Check description text for Fair Housing issues. That needs Legal and Compliance involved first.

## Seeded problems in the sample data
| Listing | Problem | Expected result |
|---|---|---|
| L1001 | Price shown as $752,000 on portal_b | Critical |
| L1002 | Brand site says For Sale, MLS says Pending | Critical |
| L1003 | Hidden address shows on portal_a | Critical |
| L1004 | Square footage 1580 vs 1850; cut-off description | Medium, low |
| L1005 | Price changed 8 minutes before the check | Recheck |
| L1006 | Missing from brand site; shown on a site the seller did not allow | High, critical |
| L1007 | Bad values in the MLS record itself | High, run continues |

## Roadmap: alerts and self-healing (plan, not built)
This version has no Slack alert and makes no fixes. The plan:
1. **Alert.** Critical findings post to Slack (or a similar place) right away with the listing, site, field, what the MLS says, what the site shows, and a suggested next step. High findings post the same day. Medium and low go in a daily summary. A sync-delay recheck stays quiet unless it still fails.
2. **Suggest a fix.** The agent proposes the exact correction and a person approves it.
3. **Auto-fix low risk.** Only a short approved list, such as re-sending the MLS data to a site, with a re-check after every fix, a rollback, a kill switch and an audit trail.
4. **Widen slowly,** only after weeks of accurate suggestions.

**Which way fixes go:** the MLS entry made by the listing agent is the source of truth. The agent corrects the site copies to match it. It does not edit the MLS record. If the MLS entry looks wrong, it alerts the listing agent or data owner. Any write access needs Legal and MLS approval first.
