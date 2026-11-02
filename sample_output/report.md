# Listing validation report (prototype, made-up data)

Checked at: 2026-11-02T14:00:00+00:00
Listings: 7. Site checks run: 24.

| Severity | Count |
|---|---|
| critical | 4 |
| high | 3 |
| medium | 1 |
| low | 1 |
| recheck | 2 |

## Critical (4)

| Listing | Site | Field | What happened | Next step |
|---|---|---|---|---|
| L1001 | portal_b | list_price | portal_b shows '$752,000'; the MLS has 725000. | Fix now and tell the listing agent. |
| L1002 | brand_site | status | brand_site shows 'For Sale'; the MLS has 'Pending'. | Fix now and tell the listing agent. |
| L1003 | portal_a | address | The seller asked to hide the address, but it is showing. | Fix now and tell the listing agent. |
| L1006 | portal_b | syndication | The seller's instructions do not allow portal_b to show this listing. | Fix now and tell the listing agent. |

## High (3)

| Listing | Site | Field | What happened | Next step |
|---|---|---|---|---|
| L1006 | brand_site | listing | brand_site should show this listing but does not. | Review today. |
| L1007 | MLS | list_price | The MLS record itself has a problem: price not readable: 'N/A'. Not compared. | Review today. |
| L1007 | MLS | beds | The MLS record itself has a problem: number missing. Not compared. | Review today. |

## Medium (1)

| Listing | Site | Field | What happened | Next step |
|---|---|---|---|---|
| L1004 | portal_a | sqft | portal_a shows 1580; the MLS has 1850. | Review this week. |

## Low (1)

| Listing | Site | Field | What happened | Next step |
|---|---|---|---|---|
| L1004 | brand_site | remarks | Description is cut off. | Log it. Fix when convenient. |

## Recheck (2)

| Listing | Site | Field | What happened | Next step |
|---|---|---|---|---|
| L1005 | portal_a | list_price | The MLS changed in the last 15 minutes, so portal_a may not have synced yet. | Probably a sync delay. Check again after the sync window. |
| L1005 | portal_b | list_price | The MLS changed in the last 15 minutes, so portal_b may not have synced yet. | Probably a sync delay. Check again after the sync window. |
