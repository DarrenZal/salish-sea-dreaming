#!/usr/bin/env python3
"""
create_ssd_opportunity_tracker.py
Create the SSD "Conversation / Opportunity Tracker" Notion database (per Pravin's
2026-06-11 proposal) and seed it with the two live conversations (TELUS/Justin Yang,
AGOG/Brandon Letsinger).

Prereqs:
  1. A VALID Notion internal-integration token (ntn_...). The token currently in the
     Notion MCP config + koi-sensors/.env returns 401 (rotated/expired) — refresh it at
     notion.so/my-integrations, or rotate the existing integration's secret.
  2. A Notion PAGE shared with that integration (internal integrations only see pages
     explicitly shared with them). Copy the page ID from its URL (the 32-hex after the
     last '-', or use the share link).

Usage:
  NOTION_TOKEN=ntn_xxx python3 create_ssd_opportunity_tracker.py --parent-page <PAGE_ID>
  NOTION_TOKEN=ntn_xxx python3 create_ssd_opportunity_tracker.py --parent-page <PAGE_ID> --dry-run
  # reuse an already-created DB to (re)seed rows only:
  NOTION_TOKEN=ntn_xxx python3 create_ssd_opportunity_tracker.py --db-id <DB_ID>

API client pattern mirrors scripts/shared/obsidian_to_notion.py in darren-workflow.
"""
import argparse, json, os, sys, urllib.request, urllib.error

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

OPP_TYPES = ["Presentation", "Conference", "Installation", "Partnership",
             "Funding", "Institutional", "Documentation", "Other"]
DECISION_STATUS = ["New", "Under internal review", "In progress",
                   "Approved to proceed", "On hold", "Declined", "Done"]


def notion(token, method, path, payload=None):
    req = urllib.request.Request(
        f"{NOTION_API}{path}",
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION,
                 "Content-Type": "application/json"},
        method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Notion {method} {path} -> {e.code}: {e.read().decode()[:400]}")


def _rt(text):
    return {"rich_text": [{"type": "text", "text": {"content": str(text)[:2000]}}]}


# ── Database schema (Pravin's suggested fields) ──────────────────────────────
DB_PROPERTIES = {
    "Contact / Organization":            {"title": {}},
    "Conversation lead":                 {"rich_text": {}},
    "Date":                              {"date": {}},
    "Opportunity type":                  {"select": {"options": [{"name": n} for n in OPP_TYPES]}},
    "Summary":                           {"rich_text": {}},
    "Requests / proposals":              {"rich_text": {}},
    "Commitments made or implied":       {"rich_text": {}},
    "Artists / cultural materials":      {"rich_text": {}},
    "Budget implications":               {"rich_text": {}},
    "Internal lead":                     {"rich_text": {}},
    "Required consultations":            {"rich_text": {}},
    "Decision status":                   {"select": {"options": [{"name": n} for n in DECISION_STATUS]}},
    "Next steps":                        {"rich_text": {}},
    "Supporting notes / links":          {"rich_text": {}},
}


def row(contact, lead, date, otype, summary, requests, commitments, artists,
        budget, internal_lead, consultations, status, next_steps, notes):
    return {
        "Contact / Organization": {"title": [{"type": "text", "text": {"content": contact}}]},
        "Conversation lead": _rt(lead),
        "Date": {"date": {"start": date}},
        "Opportunity type": {"select": {"name": otype}},
        "Summary": _rt(summary),
        "Requests / proposals": _rt(requests),
        "Commitments made or implied": _rt(commitments),
        "Artists / cultural materials": _rt(artists),
        "Budget implications": _rt(budget),
        "Internal lead": _rt(internal_lead),
        "Required consultations": _rt(consultations),
        "Decision status": {"select": {"name": status}},
        "Next steps": _rt(next_steps),
        "Supporting notes / links": _rt(notes),
    }


SEED_ROWS = [
    row(
        contact="Justin Yang — TELUS (Data & Trust Office)",
        lead="Darren Zal",
        date="2026-06-01",
        otype="Presentation",
        summary=("Met Justin Yang at Indigenomics IMPACT; he was struck by SSD and our use of the "
                 "TELUS sovereign AI factory. Invited Darren to present in TELUS's bi-weekly AI "
                 "education series. Colleague Marisa Generoso then offered scheduling options."),
        requests=("Present SSD + the TELUS sovereign AI factory connection in the TELUS AI education "
                  "series. Dates offered: June 18 or 25, 2pm ET. They asked for a speaker intro/bio."),
        commitments="Darren accepted in principle (Jun 5). No date, scope, or bios confirmed yet.",
        artists="SSD work shown; Coast Salish co-authorship referenced. Keep cultural material general pending consent.",
        budget="TELUS = corporate-sponsor potential. No funding ask on the table yet.",
        internal_lead="Darren (Natalia to be looped in per the corporate-sponsor protocol)",
        consultations="Natalia (institutional/corporate); internal review BEFORE confirming a date/scope/bios.",
        status="Under internal review",
        next_steps=("Loop Natalia in; internal review of scope; send holding reply to Marisa; then confirm "
                    "a date + bios. Dovetails with the upcoming TELUS GPU meeting."),
        notes="Gmail thread w/ Justin Yang + Marisa Generoso (Jun 1-11, zaldarren@gmail.com).",
    ),
    row(
        contact="Brandon Letsinger — Regenerate Cascadia / Cascadia Dept of Bioregion",
        lead="Darren Zal",
        date="2026-06-04",
        otype="Funding",
        summary=("Brandon flagged the AGOG 'Climate Futures + Immersive Media' open call ($25K-$200K). "
                 "Proposed an exhibit tour with the Cascadia landscape groups; we'd extend with a capstone "
                 "at the Turtle Island Bioregional Congress (Sept 2026) + an open toolkit. Dept of Bioregion "
                 "(US 501c3) as fiscal sponsor / receiving entity."),
        requests="Apply to AGOG via Dept of Bioregion; landscape-group exhibit tour; TIBC11 capstone; open toolkit.",
        commitments=("Darren replied Jun 11 (cc Pravin + Natalia) proposing to apply and asking Brandon for "
                     "entity details (EIN/signatory/fee). Intent-to-apply only; nothing committed externally."),
        artists="Coast Salish co-authorship kept general + consent-governed in the draft; no artist named/budgeted without sign-off.",
        budget="~$200K milestoned ask; fiscal-sponsor fee via Dept of Bioregion (within cap; % TBD).",
        internal_lead="Darren (Natalia = budget; Pravin = creative/consent)",
        consultations="Pravin (framing/consent); Natalia (budget); Austin / Coast Salish consent before any cultural specifics.",
        status="In progress",
        next_steps=("Await Brandon's entity details; Natalia finalizes budget; submit on Submittable before "
                    "Jun 12 11:59pm PT."),
        notes="Packet: docs/grants/agog-opencall-2026/. agog.org/opencall2026 ; tibc11.earth ; sent email 19eba52d30c11e9d.",
    ),
]


def main():
    ap = argparse.ArgumentParser(description="Create + seed the SSD Opportunity Tracker in Notion")
    ap.add_argument("--parent-page", help="Notion page ID to create the database under (page must be shared with the integration)")
    ap.add_argument("--db-id", help="Existing database ID to seed rows into (skip creation)")
    ap.add_argument("--token", default=os.environ.get("NOTION_TOKEN"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print("DRY RUN — database properties:")
        print(json.dumps(DB_PROPERTIES, indent=2))
        print(f"\nWould seed {len(SEED_ROWS)} rows:")
        for r in SEED_ROWS:
            print("  •", r["Contact / Organization"]["title"][0]["text"]["content"])
        return

    if not args.token:
        sys.exit("Error: no token. Set NOTION_TOKEN or pass --token (must be a VALID ntn_... secret).")
    if not args.parent_page and not args.db_id:
        sys.exit("Error: pass --parent-page <id> to create the DB, or --db-id <id> to seed an existing one.")

    db_id = args.db_id
    if not db_id:
        print(f"Creating database under page {args.parent_page} …")
        db = notion(args.token, "POST", "/databases", {
            "parent": {"type": "page_id", "page_id": args.parent_page},
            "title": [{"type": "text", "text": {"content": "SSD — Conversation & Opportunity Tracker"}}],
            "properties": DB_PROPERTIES,
        })
        db_id = db["id"]
        print(f"  database created: {db.get('url', db_id)}")

    print(f"Seeding {len(SEED_ROWS)} rows into {db_id} …")
    for r in SEED_ROWS:
        page = notion(args.token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": r})
        print("  + row:", r["Contact / Organization"]["title"][0]["text"]["content"], "->", page.get("url", page["id"]))
    print("Done.")


if __name__ == "__main__":
    main()
