# Redrob Hackathon — Intelligent Candidate Ranking System

A rule-based, multi-component candidate scoring system for the **Senior AI Engineer — Founding Team** role at Redrob AI.

## Overview

This ranker evaluates 100,000 candidates across 7 scoring dimensions:

| Component | Max Score | What It Measures |
|-----------|-----------|------------------|
| Title & Career Fit | 30 pts | Current title relevance, career trajectory at product companies, evidence of shipping ML systems |
| Skills Match | 25 pts | Relevant skills with trust-weighted scoring (endorsements × duration) |
| Experience Band | 15 pts | Years of experience fitting the 5-9 year ideal range |
| Location & Logistics | 10 pts | Geographic proximity, relocation willingness, notice period |
| Education | 5 pts | Relevant field, institution tier, advanced degree |
| Behavioral Signals | 0.3-1.2x | Multiplicative modifier based on platform engagement |
| Honeypot Detection | Pass/Fail | Identifies impossible profiles to avoid disqualification |

**Key design decisions:**
- Title/career fit is weighted highest (30/85) because the JD explicitly warns against keyword matching
- Skills use trust-weighted scoring — "expert" with 0 endorsements is penalized, not rewarded
- Behavioral signals are multiplicative — an inactive candidate gets down-weighted regardless of skill match
- Honeypot detection uses multiple signals (≥2 flags required) to avoid false positives

## Setup

```bash
# No external dependencies needed — pure Python stdlib
python --version  # Python 3.8+ required
```

## Usage

### Reproduce the submission CSV

```bash
python rank.py --candidates ../India_runs_data_and_ai_challenge/candidates.jsonl --out ./submission.csv
```

### Run on sample data (for quick testing)

```bash
python rank.py --candidates ../India_runs_data_and_ai_challenge/sample_candidates.json --out ./test_submission.csv --verbose
```

### With gzipped input

```bash
python rank.py --candidates ../India_runs_data_and_ai_challenge/candidates.jsonl.gz --out ./submission.csv
```

### Validate the submission

```bash
python ../India_runs_data_and_ai_challenge/validate_submission.py ./submission.csv
```

## Architecture

```
redrob_ranker/
├── rank.py          # CLI entry point: load → score → sort → write CSV
├── scorer.py        # 7-component scoring engine
├── reasoning.py     # Generates varied, specific reasoning text
├── config.py        # All weights, keyword lists, thresholds
├── requirements.txt # Dependencies (stdlib only)
└── README.md        # This file
```

## Compute Profile

- **Runtime**: ~30-60 seconds for 100K candidates on modern CPU
- **Memory**: <2 GB (streaming, no full dataset in memory at once)
- **CPU only**: No GPU required
- **No network**: No external API calls
- **Pure Python**: No compiled dependencies

## Methodology

### Why rule-based instead of embedding-based?

The JD explicitly warns that keyword embedding approaches fall into traps in this dataset. The scoring system needs to reason about:
- Career trajectory (consulting-only is a disqualifier)
- Title/description mismatches (Marketing Manager listing AI skills)
- Behavioral availability (inactive candidates are not hirable)

These are structural checks that embeddings can't perform. A rule-based system with carefully designed scoring components achieves this while running in seconds on CPU.
