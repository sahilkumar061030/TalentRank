#!/usr/bin/env python3
"""
rank.py — Main entry point for the Redrob candidate ranker.

Reads candidate profiles from JSONL (or gzipped JSONL), scores each one
against the Senior AI Engineer JD, selects the top 100, and writes a
submission CSV.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
    python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
"""

import argparse
import csv
import gzip
import json
import os
import sys
import time

# Ensure we can import sibling modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scorer import score_candidate
from reasoning import generate_reasoning


def load_candidates(path):
    """
    Load candidates from a JSONL file (or gzipped JSONL, or JSON array).
    Yields candidate dicts one at a time.
    """
    # Detect format
    if path.endswith(".gz"):
        opener = lambda: gzip.open(path, "rt", encoding="utf-8")
    elif path.endswith(".json"):
        # JSON array — load whole file
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            yield item
        return
    else:
        opener = lambda: open(path, "r", encoding="utf-8")

    with opener() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  [WARN] Skipping line {line_num}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Rank candidates for the Senior AI Engineer role."
    )
    parser.add_argument(
        "--candidates", required=True,
        help="Path to candidates.jsonl, candidates.jsonl.gz, or sample_candidates.json"
    )
    parser.add_argument(
        "--out", required=True,
        help="Output CSV path (e.g., ./submission.csv)"
    )
    parser.add_argument(
        "--top-n", type=int, default=100,
        help="Number of top candidates to output (default: 100)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print detailed progress and top candidate info"
    )
    args = parser.parse_args()

    print(f"=== Redrob Candidate Ranker ===")
    print(f"Input:  {args.candidates}")
    print(f"Output: {args.out}")
    print(f"Top-N:  {args.top_n}")
    print()

    # --- Phase 1: Score all candidates ---
    start_time = time.time()
    scored = []
    honeypot_count = 0
    total_count = 0

    print("Phase 1: Scoring candidates...")
    for candidate in load_candidates(args.candidates):
        total_count += 1
        cid = candidate.get("candidate_id", "UNKNOWN")

        result = score_candidate(candidate)
        scored.append((cid, result, candidate))

        if result["is_honeypot"]:
            honeypot_count += 1

        if total_count % 10000 == 0:
            elapsed = time.time() - start_time
            print(f"  Scored {total_count:,} candidates ({elapsed:.1f}s elapsed)")

    score_time = time.time() - start_time
    print(f"  Done: {total_count:,} candidates scored in {score_time:.1f}s")
    print(f"  Honeypots detected: {honeypot_count}")
    print()

    # --- Phase 2: Sort and select top N ---
    print(f"Phase 2: Selecting top {args.top_n}...")
    # Sort by total_score descending; break ties by candidate_id ascending
    scored.sort(key=lambda x: (-x[1]["total_score"], x[0]))

    top_n = scored[:args.top_n]

    if args.verbose:
        print("\n  Top 10 candidates:")
        for i, (cid, result, cand) in enumerate(top_n[:10], 1):
            title = cand.get("profile", {}).get("current_title", "?")
            yoe = cand.get("profile", {}).get("years_of_experience", 0)
            loc = cand.get("profile", {}).get("location", "?")
            print(f"    #{i}: {cid} | {title} | {yoe:.1f}yr | {loc} | "
                  f"score={result['total_score']:.2f} "
                  f"(raw={result['raw_sum']:.1f} × {result['behavioral_multiplier']:.2f})")
        print()

    # --- Phase 3: Generate reasoning and write CSV ---
    print(f"Phase 3: Writing {args.out}...")

    # Compute normalized scores (rank 1 gets highest, rank 100 gets lowest)
    max_score = top_n[0][1]["total_score"] if top_n else 1.0
    min_score = top_n[-1][1]["total_score"] if top_n else 0.0
    score_range = max_score - min_score if max_score > min_score else 1.0

    rows = []
    for rank, (cid, result, candidate) in enumerate(top_n, 1):
        # Normalize score to 0-1 range (non-increasing with rank)
        normalized_score = round(
            0.2 + 0.8 * (result["total_score"] - min_score) / score_range,
            4
        )
        reasoning = generate_reasoning(candidate, result, rank)
        rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": normalized_score,
            "reasoning": reasoning,
        })

    # Ensure scores are strictly non-increasing (fix floating point issues)
    for i in range(1, len(rows)):
        if rows[i]["score"] > rows[i - 1]["score"]:
            rows[i]["score"] = rows[i - 1]["score"]

    # Tie-break: if same score, ensure candidate_id is ascending
    for i in range(1, len(rows)):
        if (rows[i]["score"] == rows[i - 1]["score"]
                and rows[i]["candidate_id"] < rows[i - 1]["candidate_id"]):
            # Slightly decrease this score to break the tie
            rows[i]["score"] = round(rows[i]["score"] - 0.0001, 4)

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        writer.writerows(rows)

    total_time = time.time() - start_time
    print(f"  Done: {len(rows)} rows written to {args.out}")
    print(f"\nTotal runtime: {total_time:.1f}s")

    # --- Summary stats ---
    if rows:
        print(f"\nScore range: {rows[0]['score']:.4f} (rank 1) -> {rows[-1]['score']:.4f} (rank {len(rows)})")

    # Check for honeypots in top 100
    hp_in_top = sum(1 for _, result, _ in top_n if result["is_honeypot"])
    if hp_in_top > 0:
        print(f"\n[WARNING] {hp_in_top} honeypot(s) detected in top {args.top_n}!")
    else:
        print(f"\n[OK] No honeypots in top {args.top_n}")

    print("\n=== Complete ===")


if __name__ == "__main__":
    main()
