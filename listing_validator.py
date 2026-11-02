#!/usr/bin/env python3
"""Listing validation prototype.

Compares what the MLS record says (source of truth) against what each site shows.
Exact fields are checked by plain rules. No LLM is called in this version.
Everything it flags goes to a person. It never changes a listing.

Runs on MADE-UP data only. Not production. Not MLS data.
"""
import argparse
import csv
import json
import os
import re
from datetime import datetime, timedelta, timezone

# field -> severity when it does not match
FIELDS = [
    ("status", "critical"),
    ("list_price", "critical"),
    ("address", "high"),
    ("beds", "high"),
    ("baths", "high"),
    ("sqft", "medium"),
    ("remarks", "low"),
]
SEVERITY_ORDER = ["critical", "high", "medium", "low", "recheck"]
ACTION = {
    "critical": "Fix now and tell the listing agent.",
    "high": "Review today.",
    "medium": "Review this week.",
    "low": "Log it. Fix when convenient.",
    "recheck": "Probably a sync delay. Check again after the sync window.",
}

STATUS_MAP = {
    "active": "active", "for sale": "active", "new": "active", "coming soon": "coming_soon",
    "pending": "pending", "under contract": "pending", "sale pending": "pending",
    "sold": "sold", "closed": "sold",
    "withdrawn": "off", "off market": "off", "canceled": "off", "cancelled": "off",
}
ADDR_ABBR = {"street": "st", "avenue": "ave", "road": "rd", "drive": "dr", "lane": "ln",
             "court": "ct", "boulevard": "blvd", "place": "pl", "terrace": "ter"}


class Unreadable(Exception):
    """A value is missing or cannot be understood."""


def norm_price(v):
    if v is None or isinstance(v, bool):
        raise Unreadable("price missing")
    if isinstance(v, (int, float)):
        return int(round(v))
    s = str(v).strip().lower().replace(",", "").replace("$", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([km]?)", s)
    if not m:
        raise Unreadable(f"price not readable: {v!r}")
    return int(round(float(m.group(1)) * {"": 1, "k": 1_000, "m": 1_000_000}[m.group(2)]))


def norm_num(v):
    if v is None or isinstance(v, bool):
        raise Unreadable("number missing")
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.]", "", str(v))
    if not s:
        raise Unreadable(f"number not readable: {v!r}")
    return float(s)


def norm_status(v):
    if v is None:
        raise Unreadable("status missing")
    key = re.sub(r"\s+", " ", str(v).strip().lower())
    if key not in STATUS_MAP:
        raise Unreadable(f"unknown status: {v!r}")
    return STATUS_MAP[key]


def norm_address(v):
    if v is None:
        raise Unreadable("address missing")
    words = re.sub(r"[^\w\s]", " ", str(v).lower()).split()
    return " ".join(ADDR_ABBR.get(w, w) for w in words)


def norm_text(v):
    if v is None:
        raise Unreadable("text missing")
    return re.sub(r"\s+", " ", str(v)).strip()


NORMALIZERS = {"status": norm_status, "list_price": norm_price, "address": norm_address,
               "beds": norm_num, "baths": norm_num, "sqft": norm_num, "remarks": norm_text}


def parse_time(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def finding(listing_id, site, field, kind, severity, expected, shown, note):
    return {"listing_id": listing_id, "site": site, "field": field, "kind": kind,
            "severity": severity, "expected": expected, "shown": shown, "note": note,
            "action": ACTION[severity]}


def validate_listing(mls, displays, check_time, sync_window_min=15):
    """Returns (findings, audit_rows) for one MLS listing across every site."""
    lid = mls["listing_id"]
    findings, audit = [], []
    recently_changed = parse_time(mls["last_modified"]) >= check_time - timedelta(minutes=sync_window_min)
    allowed = set(mls.get("syndicate_to", []))
    try:
        mls_status = norm_status(mls.get("status"))
    except Unreadable:
        mls_status = None

    # Fields in the source record that cannot be read are flagged once, then skipped.
    source_ok = {}
    for field, sev in FIELDS:
        try:
            source_ok[field] = NORMALIZERS[field](mls.get(field))
        except Unreadable as e:
            findings.append(finding(lid, "MLS", field, "source_unreadable", "high",
                                    mls.get(field), None,
                                    f"The MLS record itself has a problem: {e}. Not compared."))

    for site, shown_all in displays.items():
        shown = shown_all.get(lid)
        expected_present = mls_status in ("active", "pending", "coming_soon") and site in allowed
        if shown is None:
            if expected_present:
                findings.append(finding(lid, site, "listing", "missing_listing", "high",
                                        "shown", "not shown",
                                        f"{site} should show this listing but does not."))
            audit.append({"listing_id": lid, "site": site, "result": "not_shown",
                          "expected_present": expected_present})
            continue

        if site not in allowed:
            findings.append(finding(lid, site, "syndication", "instruction_violation", "critical",
                                    f"only {sorted(allowed)}", "shown",
                                    f"The seller's instructions do not allow {site} to show this listing."))

        checked = 0
        for field, sev in FIELDS:
            if field not in source_ok:
                continue
            if field == "address" and mls.get("hide_address"):
                try:
                    shown_addr = norm_address(shown.get("address"))
                except Unreadable:
                    shown_addr = ""
                if source_ok["address"] in shown_addr:
                    findings.append(finding(lid, site, "address", "instruction_violation", "critical",
                                            "address hidden", shown.get("address"),
                                            "The seller asked to hide the address, but it is showing."))
                checked += 1
                continue
            checked += 1
            try:
                got = NORMALIZERS[field](shown.get(field))
            except Unreadable as e:
                findings.append(finding(lid, site, field, "shown_unreadable", sev,
                                        mls.get(field), shown.get(field), f"{site}: {e}."))
                continue
            want = source_ok[field]
            if got == want:
                continue
            if field == "remarks" and shown.get(field) and str(shown[field]).rstrip().endswith(("...", "…")):
                stem = norm_text(str(shown[field]).rstrip(". …"))
                if want.startswith(stem):
                    findings.append(finding(lid, site, field, "truncated", "low", mls.get(field),
                                            shown.get(field), "Description is cut off."))
                    continue
            if recently_changed:
                findings.append(finding(lid, site, field, "possible_sync_lag", "recheck",
                                        mls.get(field), shown.get(field),
                                        f"The MLS changed in the last {sync_window_min} minutes, "
                                        f"so {site} may not have synced yet."))
            else:
                findings.append(finding(lid, site, field, "mismatch", sev, mls.get(field),
                                        shown.get(field), f"{site} shows {shown.get(field)!r}; "
                                        f"the MLS has {mls.get(field)!r}."))
        audit.append({"listing_id": lid, "site": site, "result": "checked", "fields_checked": checked})
    return findings, audit


def run(mls_path, displays_path, check_time, out_dir, sync_window_min=15):
    with open(mls_path) as f:
        listings = json.load(f)["listings"]
    with open(displays_path) as f:
        displays = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    all_findings, all_audit = [], []
    for item in listings:
        try:
            fnd, aud = validate_listing(item, displays, check_time, sync_window_min)
        except Exception as e:  # one bad record must not stop the run or disappear
            lid = item.get("listing_id", "unknown") if isinstance(item, dict) else "unknown"
            fnd = [finding(lid, "validator", "record", "validator_error", "high", None, None,
                           f"The validator could not process this record: {type(e).__name__}: {e}")]
            aud = [{"listing_id": lid, "site": "validator", "result": "error"}]
        all_findings += fnd
        all_audit += aud
    all_findings.sort(key=lambda x: (SEVERITY_ORDER.index(x["severity"]), x["listing_id"], x["site"]))
    os.makedirs(out_dir, exist_ok=True)
    stamp = check_time.isoformat()
    with open(os.path.join(out_dir, "audit_log.jsonl"), "w") as f:
        for row in all_audit:
            f.write(json.dumps({"checked_at": stamp, **row}) + "\n")
    cols = ["severity", "listing_id", "site", "field", "kind", "expected", "shown", "note", "action"]
    with open(os.path.join(out_dir, "findings.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(all_findings)
    write_report(os.path.join(out_dir, "report.md"), all_findings, all_audit, len(listings), stamp)
    return all_findings, all_audit


def write_report(path, findings, audit, n_listings, stamp):
    counts = {s: sum(1 for x in findings if x["severity"] == s) for s in SEVERITY_ORDER}
    checked = sum(1 for a in audit if a["result"] == "checked")
    lines = ["# Listing validation report (prototype, made-up data)", "",
             f"Checked at: {stamp}", f"Listings: {n_listings}. Site checks run: {checked}.", "",
             "| Severity | Count |", "|---|---|"]
    lines += [f"| {s} | {counts[s]} |" for s in SEVERITY_ORDER]
    for s in SEVERITY_ORDER:
        rows = [x for x in findings if x["severity"] == s]
        if not rows:
            continue
        lines += ["", f"## {s.capitalize()} ({len(rows)})", "",
                  "| Listing | Site | Field | What happened | Next step |", "|---|---|---|---|---|"]
        for x in rows:
            lines.append(f"| {x['listing_id']} | {x['site']} | {x['field']} | {x['note']} | {x['action']} |")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--mls", default=os.path.join(here, "mls_listings.json"))
    ap.add_argument("--displays", default=os.path.join(here, "site_displays.json"))
    ap.add_argument("--check-time", default="2026-11-02T14:00:00Z")
    ap.add_argument("--out-dir", default=os.path.join(here, "output"))
    ap.add_argument("--sync-window-min", type=int, default=15)
    a = ap.parse_args()
    fnd, _ = run(a.mls, a.displays, parse_time(a.check_time), a.out_dir, a.sync_window_min)
    print(f"{len(fnd)} findings. Report: {os.path.join(a.out_dir, 'report.md')}")
