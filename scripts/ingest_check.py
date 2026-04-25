#!/usr/bin/env python3
"""
ingest_check.py — Validate proposed additions to the chat-RAG corpus and
report keyword-coverage gaps.

Reproduces the keyword-matching algorithm used by `find_relevant_context`
in `gallery_server.py` so that authors of new cards / context-doc chunks
can sanity-check whether their content will actually surface for the
expected user queries before deploying.

Algorithm (see scripts/gallery_server.py, ~line 377):
  - Tokenize lowercased query, keep [a-z]+ tokens > 2 chars.
  - Drop a hard-coded stopword list.
  - For each card (title + body + subtitle + nid) and each doc chunk
    (title + text), score by:
        +2 if any token is a substring of the text
        +1 if first 4 chars of token appear AND len(token) >= 4
    Threshold to surface: score >= 3.
  - Require at least 2 meaningful tokens; otherwise return ([], []).

Exit codes:
  0 — every query has at least one match (cards OR docs)
  1 — at least one query has NO matches (coverage gap)
  2 — JSON validation failed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Matching algorithm — kept in sync with scripts/gallery_server.py
# ---------------------------------------------------------------------------

STOPWORDS = {
    'the', 'is', 'on', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for',
    'it', 'do', 'how', 'what', 'who', 'why', 'can', 'are', 'was', 'has',
    'this', 'that', 'with', 'about', 'does', 'used', 'using', 'made',
    'make', 'like', 'many', 'much', 'some', 'also', 'been', 'from',
    'they', 'them', 'their', 'there', 'here', 'would', 'could', 'should',
    'which', 'where', 'when', 'will', 'just', 'than', 'then', 'into',
    'over', 'such', 'only', 'very', 'more', 'most', 'other', 'these',
    'those',
}


def tokenize(query: str) -> list[str]:
    raw_tokens = re.findall(r'[a-z]+', query.lower())
    return [t for t in raw_tokens if len(t) > 2 and t not in STOPWORDS]


def score_text(tokens: list[str], text: str) -> int:
    text = text.lower()
    score = 0
    for t in tokens:
        if t in text:
            score += 2
        elif len(t) >= 4 and t[:4] in text:
            score += 1
    return score


def find_relevant_context(
    query: str,
    cards: dict,
    docs: list,
    top_k_cards: int = 3,
    top_k_docs: int = 3,
) -> tuple[list[tuple[int, str, dict]], list[tuple[int, dict]], list[str]]:
    """Returns (top_cards, top_docs, tokens_used)."""
    tokens = tokenize(query)
    if len(tokens) < 2:
        return [], [], tokens

    card_scores: list[tuple[int, str, dict]] = []
    for nid, card in cards.items():
        if not isinstance(card, dict):
            continue
        text = (
            f"{card.get('title', '')} "
            f"{card.get('body', '')} "
            f"{card.get('subtitle', '')} "
            f"{nid}"
        )
        s = score_text(tokens, text)
        if s >= 3:
            card_scores.append((s, nid, card))
    card_scores.sort(key=lambda x: x[0], reverse=True)

    doc_scores: list[tuple[int, dict]] = []
    for chunk in docs:
        if not isinstance(chunk, dict):
            continue
        text = f"{chunk.get('title', '')} {chunk.get('text', '')}"
        s = score_text(tokens, text)
        if s >= 3:
            doc_scores.append((s, chunk))
    doc_scores.sort(key=lambda x: x[0], reverse=True)

    return card_scores[:top_k_cards], doc_scores[:top_k_docs], tokens


# ---------------------------------------------------------------------------
# Loading + validation
# ---------------------------------------------------------------------------


def load_cards(path: Path) -> tuple[dict, list[str]]:
    """Returns (cards_dict, errors). cards_dict is the inner card map."""
    errors: list[str] = []
    try:
        with open(path) as f:
            raw = json.load(f)
    except Exception as e:
        return {}, [f"cards: failed to read/parse {path}: {e}"]

    if not isinstance(raw, dict):
        return {}, [f"cards: top-level must be a dict, got {type(raw).__name__}"]

    if 'cards' in raw:
        cards = raw['cards']
        if not isinstance(cards, dict):
            errors.append(
                f"cards: top-level 'cards' key must be a dict, got "
                f"{type(cards).__name__}"
            )
            return {}, errors
    else:
        # Flat dict — treat raw as the card map
        cards = raw

    bad = 0
    for nid, card in cards.items():
        if not isinstance(card, dict):
            bad += 1
            continue
        if 'title' not in card and 'body' not in card:
            # Tolerate missing fields, but flag if a card has neither
            errors.append(
                f"cards: entry '{nid}' has neither 'title' nor 'body'"
            )
    if bad:
        errors.append(f"cards: {bad} entries are not objects")

    return cards, errors


def load_docs(path: Path) -> tuple[list, list[str]]:
    errors: list[str] = []
    try:
        with open(path) as f:
            raw = json.load(f)
    except Exception as e:
        return [], [f"docs: failed to read/parse {path}: {e}"]

    if not isinstance(raw, list):
        return [], [f"docs: top-level must be a list, got {type(raw).__name__}"]

    required = ('id', 'title', 'text')
    bad = 0
    for i, chunk in enumerate(raw):
        if not isinstance(chunk, dict):
            errors.append(f"docs: chunk #{i} is not a dict")
            bad += 1
            continue
        missing = [k for k in required if k not in chunk]
        if missing:
            errors.append(
                f"docs: chunk #{i} (id={chunk.get('id', '<none>')}) "
                f"missing fields: {missing}"
            )
            bad += 1
    return raw, errors


def load_queries(path: Path) -> list[str]:
    with open(path) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith('#')
        ]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

# Concept cards the morning team should confirm exist & surface.
# (Stub — humans should populate this list as the corpus grows.)
EXPECTED_CONCEPT_CARDS = [
    "concept:hakini-mudra",
    "concept:sympoiesis",
    "concept:kwaxala",
    "concept:mutual-release",
    "concept:asymmetric-break",
    "concept:side-a-side-b",
    "concept:indigenomics",
    "concept:co-dreaming",
    "concept:three-eyed-seeing",
    "concept:tlep",
]


def render_report(
    queries: list[str],
    results: list[dict],
    cards_path: Path,
    docs_path: Path,
    cards_count: int,
    docs_count: int,
    cards: dict,
) -> str:
    lines: list[str] = []
    lines.append("# Chat-RAG Ingest Coverage Report")
    lines.append("")
    lines.append(f"- **Cards source:** `{cards_path}` ({cards_count} cards)")
    lines.append(f"- **Docs source:** `{docs_path}` ({docs_count} doc chunks)")
    lines.append(f"- **Queries:** {len(queries)}")
    lines.append("")

    matched = [r for r in results if r['top_cards'] or r['top_docs']]
    no_match = [r for r in results if not (r['top_cards'] or r['top_docs'])]
    too_thin = [r for r in results if len(r['tokens']) < 2]

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total queries: **{len(queries)}**")
    lines.append(f"- Queries with at least 1 match: **{len(matched)}**")
    lines.append(f"- Queries with NO MATCHES: **{len(no_match)}**")
    if too_thin:
        lines.append(
            f"- Queries with < 2 meaningful tokens (auto-skipped, system-prompt-only): "
            f"**{len(too_thin)}**"
        )
    lines.append("")

    # Coverage gaps section — most actionable
    lines.append("## Coverage Gaps (NO MATCHES)")
    lines.append("")
    lines.append(
        "These queries will fall back to system-prompt-only responses. "
        "Add cards or doc chunks whose title/body contains the listed tokens "
        "to lift them above the threshold (score >= 3)."
    )
    lines.append("")
    if not no_match:
        lines.append("_None — every query matched at least one card or doc._")
    else:
        for r in no_match:
            tok_str = ", ".join(r['tokens']) if r['tokens'] else "(too few tokens)"
            lines.append(f"- **`{r['query']}`** — tokens: _{tok_str}_")
    lines.append("")

    # Per-query breakdown
    lines.append("## Per-Query Breakdown")
    lines.append("")
    for r in results:
        lines.append(f"### `{r['query']}`")
        tok_str = ", ".join(r['tokens']) if r['tokens'] else "(none)"
        lines.append(f"- Tokens after stopword removal: _{tok_str}_")
        if len(r['tokens']) < 2:
            lines.append(
                "- **Skipped** — fewer than 2 meaningful tokens; "
                "RAG path returns empty by design."
            )
            lines.append("")
            continue
        if r['top_cards']:
            lines.append("- **Top cards:**")
            for score, nid, card in r['top_cards']:
                title = card.get('title', '(untitled)')
                lines.append(f"  - score={score} `{nid}` — {title}")
        else:
            lines.append("- **Top cards:** _none above threshold_")
        if r['top_docs']:
            lines.append("- **Top docs:**")
            for score, chunk in r['top_docs']:
                did = chunk.get('id', '(no-id)')
                title = chunk.get('title', '(untitled)')
                lines.append(f"  - score={score} `{did}` — {title}")
        else:
            lines.append("- **Top docs:** _none above threshold_")
        if not r['top_cards'] and not r['top_docs']:
            lines.append("- **NO MATCHES** — coverage gap.")
        lines.append("")

    # Sanity check on expected concept cards
    lines.append("## Sanity Check: Expected Concept Cards")
    lines.append("")
    lines.append(
        "These keys are the morning-team's canonical list of concept cards "
        "we expect to exist in `ssd-cards.json`. If a key is **MISSING**, "
        "either the card has not been authored yet OR the slug differs."
    )
    lines.append("")
    lines.append("<!-- TODO: populate / curate this list as the corpus grows -->")
    lines.append("")
    for key in EXPECTED_CONCEPT_CARDS:
        present = key in cards
        marker = "[x]" if present else "[ ]"
        status = "PRESENT" if present else "MISSING"
        lines.append(f"- {marker} `{key}` — **{status}**")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Validate proposed additions to the chat-RAG corpus and report "
            "keyword-coverage gaps."
        )
    )
    p.add_argument("--cards", required=True, type=Path,
                   help="Path to candidate ssd-cards.json")
    p.add_argument("--docs", required=True, type=Path,
                   help="Path to candidate ssd-context-docs.json")
    p.add_argument("--queries", required=True, type=Path,
                   help="Path to text file, one expected user query per line")
    p.add_argument("--report", type=Path, default=None,
                   help="Path for markdown report (default: stdout)")
    args = p.parse_args(argv)

    # Load + validate
    cards, card_errs = load_cards(args.cards)
    docs, doc_errs = load_docs(args.docs)
    errs = card_errs + doc_errs
    if errs:
        sys.stderr.write("Validation errors:\n")
        for e in errs[:20]:
            sys.stderr.write(f"  - {e}\n")
        if len(errs) > 20:
            sys.stderr.write(f"  ... and {len(errs) - 20} more\n")
        # Only fail hard on structural errors (cards top-level / docs top-level
        # / per-doc missing required fields). Per-card "title or body missing"
        # is a soft warning — keep going only if we still have data.
        fatal = any(
            e.startswith(("cards: top-level", "cards: failed",
                          "docs: top-level", "docs: failed",
                          "docs: chunk"))
            for e in errs
        )
        if fatal or not cards or not docs:
            return 2

    queries = load_queries(args.queries)
    if not queries:
        sys.stderr.write(f"No queries found in {args.queries}\n")
        return 2

    results = []
    for q in queries:
        top_cards, top_docs, tokens = find_relevant_context(q, cards, docs)
        results.append({
            'query': q,
            'tokens': tokens,
            'top_cards': top_cards,
            'top_docs': top_docs,
        })

    report = render_report(
        queries=queries,
        results=results,
        cards_path=args.cards,
        docs_path=args.docs,
        cards_count=len(cards),
        docs_count=len(docs),
        cards=cards,
    )

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report)
        sys.stderr.write(f"Wrote report to {args.report}\n")
    else:
        sys.stdout.write(report)
        if not report.endswith("\n"):
            sys.stdout.write("\n")

    no_match_count = sum(
        1 for r in results
        if not (r['top_cards'] or r['top_docs'])
    )
    return 1 if no_match_count else 0


if __name__ == "__main__":
    sys.exit(main())
