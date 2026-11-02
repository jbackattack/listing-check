"""Stress tests for the prototype. Run: python3 test_validator.py (or pytest)."""
import json, os, tempfile
from datetime import datetime, timezone
import listing_validator as v

NOW = datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc)
BASE = {"listing_id": "T1", "status": "Active", "list_price": 500000, "address": "1 Test Ln",
        "beds": 3, "baths": 2, "sqft": 1500, "remarks": "Nice.", "last_modified": "2026-11-01T09:00:00Z",
        "hide_address": False, "syndicate_to": ["s1"]}
SHOWN = {"status": "Active", "list_price": "$500,000", "address": "1 Test Lane", "beds": 3,
         "baths": 2, "sqft": 1500, "remarks": "Nice."}


def run_one(mls=None, shown=None, site="s1"):
    mls = {**BASE, **(mls or {})}
    d = {site: {"T1": {**SHOWN, **(shown or {})}}} if shown != "MISSING" else {site: {}}
    return v.validate_listing(mls, d, NOW)[0]


def test_format_differences_are_not_flagged():
    assert run_one() == []
    assert run_one(shown={"list_price": "500000", "sqft": "1,500 sq ft", "status": "For Sale"}) == []


def test_price_transposition_is_critical():
    f = run_one(shown={"list_price": "$050,000"})
    assert [x["severity"] for x in f] == ["critical"]
    assert run_one(shown={"list_price": "$550,000"})[0]["field"] == "list_price"


def test_status_synonyms_and_real_mismatch():
    assert run_one(mls={"status": "Pending"}, shown={"status": "Under Contract"}) == []
    f = run_one(mls={"status": "Pending"}, shown={"status": "Active"})
    assert f[0]["field"] == "status" and f[0]["severity"] == "critical"


def test_bad_shown_values_are_flagged_not_crashed():
    for bad in [None, "", "TBD", "$$$", "N/A"]:
        f = run_one(shown={"list_price": bad})
        assert f and f[0]["kind"] == "shown_unreadable", bad


def test_bad_source_values_are_flagged_and_skipped():
    f = run_one(mls={"list_price": "N/A", "beds": None})
    kinds = {(x["field"], x["kind"]) for x in f}
    assert ("list_price", "source_unreadable") in kinds and ("beds", "source_unreadable") in kinds


def test_unknown_status_is_flagged():
    f = run_one(shown={"status": "Maybe"})
    assert f[0]["kind"] == "shown_unreadable"


def test_hidden_address_leak():
    f = run_one(mls={"hide_address": True}, shown={"address": "1 Test Lane"})
    assert f[0]["kind"] == "instruction_violation" and f[0]["severity"] == "critical"
    assert run_one(mls={"hide_address": True}, shown={"address": "Address withheld"}) == []


def test_syndication_not_allowed():
    f = run_one(mls={"syndicate_to": ["other"]})
    assert f[0]["kind"] == "instruction_violation"


def test_missing_listing():
    f = run_one(shown="MISSING")
    assert f[0]["kind"] == "missing_listing"
    assert run_one(shown="MISSING", mls={"syndicate_to": []}) == []


def test_sync_lag_window():
    f = run_one(mls={"last_modified": "2026-11-02T13:55:00Z"}, shown={"list_price": "$1"})
    assert f[0]["severity"] == "recheck"
    f = run_one(mls={"last_modified": "2026-11-02T13:30:00Z"}, shown={"list_price": "$1"})
    assert f[0]["severity"] == "critical"


def test_truncated_remarks_is_low():
    f = run_one(mls={"remarks": "A long description here."}, shown={"remarks": "A long..."})
    assert f[0]["kind"] == "truncated" and f[0]["severity"] == "low"


def test_one_bad_record_does_not_stop_the_run():
    with tempfile.TemporaryDirectory() as d:
        mp, dp = os.path.join(d, "m.json"), os.path.join(d, "d.json")
        json.dump({"listings": ["not a record", BASE]}, open(mp, "w"))
        json.dump({"s1": {"T1": SHOWN}}, open(dp, "w"))
        findings, audit = v.run(mp, dp, NOW, os.path.join(d, "out"))
        assert any(x["kind"] == "validator_error" for x in findings)
        assert any(a["listing_id"] == "T1" and a["result"] == "checked" for a in audit)


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print("ok  ", name)
    print(f"{len(tests)} tests passed")
