"""
reasoning.py — Generate varied, specific, honest reasoning for top-100 candidates.

Each reasoning string is 1-2 sentences that:
  - References specific facts from the candidate's profile
  - Connects to JD requirements
  - Acknowledges gaps honestly
  - Varies language across candidates
  - Matches tone to rank (enthusiastic top-10, measured 50-100)
"""

import random

# Seed for reproducibility
random.seed(42)


def _get_key_skills(details):
    """Extract the most important matched skills for mention in reasoning."""
    matched = details.get("skills", {}).get("matched_skills", [])
    if len(matched) > 4:
        return matched[:4]
    return matched


def _get_strengths(candidate, score_result):
    """Build a list of strength phrases from the scoring details."""
    strengths = []
    profile = candidate.get("profile", {})
    details = score_result["details"]
    components = score_result["component_scores"]

    # Title/career
    title = profile.get("current_title", "Unknown")
    title_tier = details["title_career"]["title_tier"]
    yoe = profile.get("years_of_experience", 0)

    if title_tier == "A":
        strengths.append(f"{title} with {yoe:.1f} years of experience")
    elif title_tier == "B":
        strengths.append(f"{title} ({yoe:.1f} yrs) with adjacent engineering background")

    # Career evidence
    desc_score = details["title_career"]["desc_score"]
    if desc_score >= 6:
        strengths.append("strong evidence of shipping production ML systems")
    elif desc_score >= 3:
        strengths.append("some production ML/AI experience in career history")

    # Skills
    matched = _get_key_skills(details)
    if matched:
        skills_str = ", ".join(matched[:3])
        strengths.append(f"relevant skills include {skills_str}")

    # Location
    city_match = details["location"].get("city_match", "")
    if city_match == "preferred":
        loc = profile.get("location", "")
        strengths.append(f"based in {loc} (preferred location)")
    elif city_match == "tier1_india":
        loc = profile.get("location", "")
        strengths.append(f"located in {loc}")

    # Education
    if details["education"]["relevant_field"]:
        edu = candidate.get("education", [{}])
        if edu:
            field = edu[0].get("field_of_study", "")
            if field:
                strengths.append(f"studied {field}")

    # Behavioral
    behavioral = details["behavioral"]
    if behavioral.get("recency_days", 999) <= 30:
        strengths.append("recently active on platform")
    if behavioral.get("github", -1) >= 40:
        strengths.append("strong GitHub activity")

    return strengths


def _get_concerns(candidate, score_result):
    """Build a list of concern phrases from the scoring details."""
    concerns = []
    profile = candidate.get("profile", {})
    details = score_result["details"]
    signals = candidate.get("redrob_signals", {})

    # Title mismatch
    title_tier = details["title_career"]["title_tier"]
    if title_tier == "C":
        concerns.append(f"current title ({profile.get('current_title', '')}) is only loosely related to the JD")
    elif title_tier == "D":
        concerns.append(f"current title ({profile.get('current_title', '')}) doesn't directly align with AI engineering")

    # Consulting-only
    if details["title_career"].get("consulting_only"):
        concerns.append("entire career at consulting/services firms")

    # Experience out of range
    yoe = profile.get("years_of_experience", 0)
    if yoe < 4:
        concerns.append(f"limited experience ({yoe:.1f} years)")
    elif yoe > 12:
        concerns.append(f"senior profile ({yoe:.1f} years) may be overqualified for IC role")

    # Location
    city_match = details["location"].get("city_match", "")
    if city_match == "international":
        country = profile.get("country", "")
        concerns.append(f"based outside India ({country})")

    # Notice period
    notice = signals.get("notice_period_days", 90)
    if notice > 60:
        concerns.append(f"notice period is {notice} days")

    # Behavioral
    behavioral = details["behavioral"]
    if behavioral.get("recency_days", 0) > 180:
        concerns.append("inactive on platform for 6+ months")
    if behavioral.get("response_rate", 1.0) < 0.3:
        rr = behavioral.get("response_rate", 0)
        concerns.append(f"low recruiter response rate ({rr:.0%})")
    if not behavioral.get("open_to_work", True):
        concerns.append("not marked as open to work")

    return concerns


# ---- Varied sentence starters and connectors ----
_STRENGTH_STARTERS_TOP = [
    "Strong fit: {strengths}.",
    "Excellent match — {strengths}.",
    "Top candidate: {strengths}.",
    "Highly aligned with JD: {strengths}.",
    "Compelling profile — {strengths}.",
]

_STRENGTH_STARTERS_MID = [
    "Solid candidate: {strengths}.",
    "Good alignment: {strengths}.",
    "Promising profile — {strengths}.",
    "Notable background: {strengths}.",
    "Reasonable fit — {strengths}.",
]

_STRENGTH_STARTERS_LOW = [
    "Partial fit: {strengths}.",
    "Some alignment — {strengths}.",
    "Borderline candidate: {strengths}.",
    "Limited match, but {strengths}.",
    "Included for: {strengths}.",
]

_CONCERN_CONNECTORS = [
    " However, {concerns}.",
    " Some concern: {concerns}.",
    " Note: {concerns}.",
    " Caveat: {concerns}.",
    " Gap: {concerns}.",
    " Consideration: {concerns}.",
]

_NO_STRENGTH_FILLER = [
    "Included based on aggregate scoring across experience, skills, and behavioral signals.",
    "Marginal candidate included to fill the top-100 pool based on composite scoring.",
    "Ranked on overall profile weight despite limited direct JD alignment.",
]


def generate_reasoning(candidate, score_result, rank):
    """
    Generate a 1-2 sentence reasoning string for a ranked candidate.

    Args:
        candidate: full candidate dict
        score_result: output of score_candidate()
        rank: integer rank (1-100)
    """
    strengths = _get_strengths(candidate, score_result)
    concerns = _get_concerns(candidate, score_result)

    # Pick sentence starters based on rank tier
    if rank <= 10:
        starters = _STRENGTH_STARTERS_TOP
    elif rank <= 50:
        starters = _STRENGTH_STARTERS_MID
    else:
        starters = _STRENGTH_STARTERS_LOW

    # Build the reasoning
    if strengths:
        # Pick a random starter (seeded, so reproducible)
        starter = starters[rank % len(starters)]
        strengths_text = "; ".join(strengths[:3])
        reasoning = starter.format(strengths=strengths_text)
    else:
        reasoning = _NO_STRENGTH_FILLER[rank % len(_NO_STRENGTH_FILLER)]

    # Add concerns if present (but keep it short)
    if concerns:
        connector = _CONCERN_CONNECTORS[rank % len(_CONCERN_CONNECTORS)]
        concerns_text = "; ".join(concerns[:2])
        reasoning += connector.format(concerns=concerns_text)

    # Ensure no double quotes that would break CSV
    reasoning = reasoning.replace('"', "'")

    # Ensure it's 1-2 sentences (cap at ~300 chars for readability)
    if len(reasoning) > 350:
        reasoning = reasoning[:347] + "..."

    return reasoning
