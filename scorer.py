"""
scorer.py — Multi-component candidate scoring engine.

Evaluates each candidate against the Senior AI Engineer JD using:
  1. Title & Career Fit (0-30 pts)
  2. Skills Match (0-25 pts)
  3. Experience Band (0-15 pts)
  4. Location & Logistics (0-10 pts)
  5. Education (0-5 pts)
  6. Behavioral Signal Multiplier (0.3-1.2x)
  7. Honeypot Detection (binary penalty)
"""

from datetime import date, timedelta
import re

from config import (
    REFERENCE_DATE,
    MAX_TITLE_CAREER_SCORE, MAX_SKILLS_SCORE, MAX_EXPERIENCE_SCORE,
    MAX_LOCATION_SCORE, MAX_EDUCATION_SCORE,
    TITLE_TIER_A, TITLE_TIER_B, TITLE_TIER_C, TITLE_TIER_SCORES,
    CAREER_KEYWORDS_HIGH, CAREER_KEYWORDS_MEDIUM,
    CONSULTING_FIRMS, PRODUCT_COMPANY_INDICATORS,
    SKILLS_CORE_ML, SKILLS_PYTHON_INFRA, SKILLS_LLM, SKILLS_EVAL_RANKING,
    SKILL_CATEGORY_MAX_POINTS,
    EXPERIENCE_BANDS,
    PREFERRED_CITIES, TIER1_INDIAN_CITIES,
    RELEVANT_EDUCATION_FIELDS, ADVANCED_DEGREES,
    RECENCY_THRESHOLDS, RESPONSE_RATE_THRESHOLDS,
    BEHAVIORAL_MULTIPLIER_FLOOR, BEHAVIORAL_MULTIPLIER_CEILING,
    HONEYPOT_EXPERT_ZERO_ENDORSEMENT_THRESHOLD,
    NON_TECH_TITLES_FOR_MISMATCH,
)


def _normalize(text):
    """Lowercase and strip for comparison."""
    return text.strip().lower() if text else ""


def _text_contains_any(text, keyword_set):
    """Check if text contains any keyword from the set. Returns count of matches."""
    text_lower = text.lower()
    count = 0
    for kw in keyword_set:
        if kw in text_lower:
            count += 1
    return count


def _parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object."""
    if not date_str:
        return None
    try:
        parts = date_str.split("-")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def _is_consulting_firm(company_name):
    """Check if a company is in the consulting firms list."""
    name = _normalize(company_name)
    for firm in CONSULTING_FIRMS:
        if firm in name or name in firm:
            return True
    return False


# ============================================================================
# Component 1: Title & Career Fit (0-30 points)
# ============================================================================

def _classify_title_tier(title):
    """Classify a job title into tier A/B/C/D."""
    t = _normalize(title)
    # Check exact and substring matches
    for tier_set, tier_name in [(TITLE_TIER_A, "A"), (TITLE_TIER_B, "B"), (TITLE_TIER_C, "C")]:
        for tier_title in tier_set:
            if tier_title in t or t in tier_title:
                return tier_name
    return "D"


def score_title_career(candidate):
    """Score based on current title, career trajectory, and career descriptions."""
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])

    # --- Current title score (0-12) ---
    current_title = profile.get("current_title", "")
    title_tier = _classify_title_tier(current_title)
    title_score = TITLE_TIER_SCORES[title_tier]

    # --- Career trajectory at product companies (0-10) ---
    total_months = 0
    product_months = 0
    consulting_months = 0
    ai_title_months = 0

    for job in career:
        dur = job.get("duration_months", 0)
        total_months += dur
        company = job.get("company", "")
        industry = job.get("industry", "")
        desc = job.get("description", "")
        job_title = job.get("title", "")

        if _is_consulting_firm(company):
            consulting_months += dur
        else:
            # Check if it's a product company
            combined = f"{company} {industry} {desc}".lower()
            if any(kw in combined for kw in PRODUCT_COMPANY_INDICATORS):
                product_months += dur

        # Check if the job title is AI/ML related
        job_tier = _classify_title_tier(job_title)
        if job_tier in ("A", "B"):
            ai_title_months += dur

    # Career trajectory score
    trajectory_score = 0.0
    if total_months > 0:
        consulting_ratio = consulting_months / total_months
        product_ratio = product_months / total_months
        ai_ratio = ai_title_months / total_months

        # Heavy penalty if entire career is consulting
        if consulting_ratio >= 0.95:
            trajectory_score = 0.5
        elif consulting_ratio >= 0.7:
            trajectory_score = 2.0
        else:
            trajectory_score = 4.0 + (product_ratio * 3.0) + (ai_ratio * 3.0)

    trajectory_score = min(trajectory_score, 10.0)

    # --- Career description evidence (0-8) ---
    all_descriptions = " ".join(job.get("description", "") for job in career)
    high_matches = _text_contains_any(all_descriptions, CAREER_KEYWORDS_HIGH)
    medium_matches = _text_contains_any(all_descriptions, CAREER_KEYWORDS_MEDIUM)

    desc_score = min(high_matches * 1.5 + medium_matches * 0.5, 8.0)

    total = title_score + trajectory_score + desc_score
    return min(total, MAX_TITLE_CAREER_SCORE), {
        "title_tier": title_tier,
        "title_score": title_score,
        "trajectory_score": round(trajectory_score, 2),
        "desc_score": round(desc_score, 2),
        "consulting_only": (consulting_months / total_months >= 0.95) if total_months > 0 else False,
    }


# ============================================================================
# Component 2: Skills Match (0-25 points)
# ============================================================================

def _skill_trust_weight(skill):
    """Calculate a trust weight for a skill claim (0.0-1.0)."""
    endorsements = skill.get("endorsements", 0)
    duration = skill.get("duration_months", 0)
    proficiency = _normalize(skill.get("proficiency", ""))

    # Expert with zero endorsements and zero/low duration = suspicious
    if proficiency == "expert" and endorsements == 0:
        return 0.1
    if proficiency == "expert" and duration < 6:
        return 0.2

    # Normal trust calculation
    trust = 0.5  # base
    if endorsements >= 10:
        trust += 0.3
    elif endorsements >= 3:
        trust += 0.15

    if duration >= 24:
        trust += 0.2
    elif duration >= 12:
        trust += 0.1

    return min(trust, 1.0)


def _match_skill_to_category(skill_name, category_set):
    """Check if a skill name matches any keyword in a category set."""
    name = _normalize(skill_name)
    for cat_kw in category_set:
        if cat_kw in name or name in cat_kw:
            return True
    return False


def score_skills(candidate):
    """Score based on skills match with trust weighting."""
    skills = candidate.get("skills", [])

    category_scores = {
        "core_ml": 0.0,
        "python_infra": 0.0,
        "llm": 0.0,
        "eval_ranking": 0.0,
    }

    category_sets = {
        "core_ml": SKILLS_CORE_ML,
        "python_infra": SKILLS_PYTHON_INFRA,
        "llm": SKILLS_LLM,
        "eval_ranking": SKILLS_EVAL_RANKING,
    }

    matched_skills = []

    for skill in skills:
        name = skill.get("name", "")
        trust = _skill_trust_weight(skill)

        for cat_name, cat_set in category_sets.items():
            if _match_skill_to_category(name, cat_set):
                # Each matched skill contributes proportional to trust
                contribution = trust * 2.5  # base contribution per skill
                category_scores[cat_name] += contribution
                matched_skills.append(name)
                break  # a skill only counts once toward one category

    # Cap each category at its max
    for cat_name in category_scores:
        category_scores[cat_name] = min(
            category_scores[cat_name],
            SKILL_CATEGORY_MAX_POINTS[cat_name]
        )

    total = sum(category_scores.values())
    total = min(total, MAX_SKILLS_SCORE)

    return total, {
        "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
        "matched_skills": matched_skills,
    }


# ============================================================================
# Component 3: Experience Band (0-15 points)
# ============================================================================

def score_experience(candidate):
    """Score based on years of experience fitting the JD's desired range."""
    yoe = candidate.get("profile", {}).get("years_of_experience", 0)

    score = 1.0  # default minimum
    for min_y, max_y, pts in EXPERIENCE_BANDS:
        if min_y <= yoe < max_y:
            score = pts
            break

    # Edge case: exactly on the max boundary of sweet spot
    if yoe == 8.0:
        score = 15.0

    return min(score, MAX_EXPERIENCE_SCORE), {"years": yoe}


# ============================================================================
# Component 4: Location & Logistics (0-10 points)
# ============================================================================

def score_location(candidate):
    """Score based on location, relocation willingness, work mode, notice period."""
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = _normalize(profile.get("location", ""))
    country = _normalize(profile.get("country", ""))

    score = 0.0
    details = {}

    # City match
    if any(city in location for city in PREFERRED_CITIES):
        score += 5.0
        details["city_match"] = "preferred"
    elif any(city in location for city in TIER1_INDIAN_CITIES):
        score += 3.0
        details["city_match"] = "tier1_india"
    elif country == "india":
        score += 2.0
        details["city_match"] = "india_other"
    else:
        score += 0.0
        details["city_match"] = "international"

    # Relocation willingness
    if signals.get("willing_to_relocate", False):
        score += 2.0
        details["relocate"] = True

    # Work mode preference
    work_mode = _normalize(signals.get("preferred_work_mode", ""))
    if work_mode in ("hybrid", "flexible"):
        score += 1.0
        details["work_mode"] = work_mode

    # Notice period
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        score += 2.0
        details["notice"] = "short"
    elif notice <= 60:
        score += 1.0
        details["notice"] = "medium"
    else:
        details["notice"] = "long"

    return min(score, MAX_LOCATION_SCORE), details


# ============================================================================
# Component 5: Education (0-5 points)
# ============================================================================

def score_education(candidate):
    """Score based on educational background relevance."""
    education = candidate.get("education", [])

    score = 0.0
    relevant_field = False
    tier_bonus = False
    advanced = False

    for edu in education:
        field = _normalize(edu.get("field_of_study", ""))
        degree = _normalize(edu.get("degree", ""))
        tier = _normalize(edu.get("tier", ""))

        # Check relevant field
        if any(rf in field for rf in RELEVANT_EDUCATION_FIELDS):
            relevant_field = True

        # Check institution tier
        if tier in ("tier_1", "tier_2"):
            tier_bonus = True

        # Check advanced degree
        if any(ad in degree for ad in ADVANCED_DEGREES):
            advanced = True

    if relevant_field:
        score += 2.0
    if tier_bonus:
        score += 2.0
    if advanced:
        score += 1.0

    return min(score, MAX_EDUCATION_SCORE), {
        "relevant_field": relevant_field,
        "tier_bonus": tier_bonus,
        "advanced_degree": advanced,
    }


# ============================================================================
# Component 6: Behavioral Signal Multiplier (0.3 - 1.2)
# ============================================================================

def compute_behavioral_multiplier(candidate):
    """Compute a multiplicative modifier based on behavioral signals."""
    signals = candidate.get("redrob_signals", {})
    multiplier = 1.0
    details = {}

    # --- Recency ---
    last_active = _parse_date(signals.get("last_active_date"))
    if last_active:
        days_ago = (REFERENCE_DATE - last_active).days
        for max_days, mult in RECENCY_THRESHOLDS:
            if days_ago <= max_days:
                multiplier *= mult
                details["recency_days"] = days_ago
                details["recency_mult"] = mult
                break

    # --- Recruiter response rate ---
    response_rate = signals.get("recruiter_response_rate", 0.5)
    for min_rate, mult in RESPONSE_RATE_THRESHOLDS:
        if response_rate >= min_rate:
            multiplier *= mult
            details["response_rate"] = response_rate
            details["response_mult"] = mult
            break

    # --- Open to work ---
    open_to_work = signals.get("open_to_work_flag", False)
    if open_to_work:
        multiplier *= 1.0
    else:
        multiplier *= 0.85
    details["open_to_work"] = open_to_work

    # --- Profile completeness ---
    completeness = signals.get("profile_completeness_score", 50)
    if completeness >= 70:
        multiplier *= 1.0
    elif completeness >= 50:
        multiplier *= 0.95
    else:
        multiplier *= 0.9
    details["completeness"] = completeness

    # --- Interview completion rate ---
    interview_rate = signals.get("interview_completion_rate", 0.5)
    if interview_rate >= 0.7:
        multiplier *= 1.0
    elif interview_rate >= 0.4:
        multiplier *= 0.95
    else:
        multiplier *= 0.85
    details["interview_rate"] = interview_rate

    # --- GitHub activity ---
    github = signals.get("github_activity_score", -1)
    if github >= 30:
        multiplier *= 1.05
    elif github == -1:
        multiplier *= 0.95
    details["github"] = github

    # --- Response time ---
    response_time = signals.get("avg_response_time_hours", 48)
    if response_time < 24:
        multiplier *= 1.05
    elif response_time > 72:
        multiplier *= 0.95
    details["response_time_hours"] = response_time

    # Clamp
    multiplier = max(BEHAVIORAL_MULTIPLIER_FLOOR,
                     min(multiplier, BEHAVIORAL_MULTIPLIER_CEILING))

    return round(multiplier, 4), details


# ============================================================================
# Component 7: Honeypot Detection
# ============================================================================

def detect_honeypot(candidate):
    """
    Detect honeypot candidates with subtly impossible profiles.
    Returns (is_honeypot: bool, reasons: list[str])
    """
    reasons = []
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})

    # --- Check 1: Expert in many skills with 0 endorsements ---
    expert_zero_endorse = sum(
        1 for s in skills
        if _normalize(s.get("proficiency", "")) == "expert"
        and s.get("endorsements", 0) == 0
    )
    if expert_zero_endorse >= HONEYPOT_EXPERT_ZERO_ENDORSEMENT_THRESHOLD:
        reasons.append(
            f"Expert in {expert_zero_endorse} skills with 0 endorsements each"
        )

    # --- Check 2: Expert proficiency with 0 duration_months ---
    expert_zero_dur = sum(
        1 for s in skills
        if _normalize(s.get("proficiency", "")) == "expert"
        and s.get("duration_months", 0) == 0
    )
    if expert_zero_dur >= 3:
        reasons.append(
            f"Expert in {expert_zero_dur} skills with 0 months duration"
        )

    # --- Check 3: Title vs description mismatch ---
    current_title = _normalize(profile.get("current_title", ""))
    is_non_tech_title = any(nt in current_title for nt in NON_TECH_TITLES_FOR_MISMATCH)

    if is_non_tech_title and career:
        # Check if descriptions mention completely unrelated work
        all_desc = " ".join(j.get("description", "") for j in career).lower()
        ai_keywords_in_desc = _text_contains_any(all_desc, CAREER_KEYWORDS_HIGH)

        # Non-tech title but claims lots of AI in descriptions is suspicious
        # However, some people transition — only flag if title AND descriptions
        # both seem mismatched
        # More importantly: check if multiple different descriptions are
        # used that don't match the stated titles
        title_desc_mismatches = 0
        for job in career:
            job_title = _normalize(job.get("title", ""))
            job_desc = job.get("description", "").lower()
            is_non_tech_job = any(nt in job_title for nt in NON_TECH_TITLES_FOR_MISMATCH)
            desc_mentions_tech = _text_contains_any(job_desc, CAREER_KEYWORDS_MEDIUM) >= 3

            if is_non_tech_job and desc_mentions_tech:
                title_desc_mismatches += 1

        if title_desc_mismatches >= 2:
            reasons.append(
                f"{title_desc_mismatches} jobs have non-tech titles but "
                f"tech-heavy descriptions (title/description mismatch)"
            )

    # --- Check 4: Many AI keywords in skills but completely non-tech career ---
    ai_skill_count = sum(
        1 for s in skills
        if _match_skill_to_category(s.get("name", ""), SKILLS_CORE_ML)
        or _match_skill_to_category(s.get("name", ""), SKILLS_LLM)
        or _match_skill_to_category(s.get("name", ""), SKILLS_EVAL_RANKING)
    )

    # Check if ALL career titles are non-tech
    all_career_non_tech = all(
        any(nt in _normalize(j.get("title", "")) for nt in NON_TECH_TITLES_FOR_MISMATCH)
        for j in career
    ) if career else False

    if ai_skill_count >= 5 and all_career_non_tech:
        reasons.append(
            f"{ai_skill_count} AI/ML skills listed but all career titles "
            f"are non-technical"
        )

    # --- Check 5: Impossibly long tenure ---
    # Some honeypots may have duration_months that exceed the time since
    # the company was "founded" — but since we don't have founding dates,
    # we check for very long tenures at what appears to be recent companies
    for job in career:
        dur = job.get("duration_months", 0)
        start = _parse_date(job.get("start_date"))
        end = _parse_date(job.get("end_date"))

        if start and end:
            actual_months = (end.year - start.year) * 12 + (end.month - start.month)
            if dur > 0 and actual_months > 0:
                if abs(dur - actual_months) > 24:
                    reasons.append(
                        f"Job at {job.get('company', '?')}: stated duration "
                        f"{dur}mo but dates span {actual_months}mo"
                    )
        elif start and job.get("is_current"):
            actual_months = (REFERENCE_DATE.year - start.year) * 12 + \
                          (REFERENCE_DATE.month - start.month)
            if dur > 0 and actual_months > 0:
                if abs(dur - actual_months) > 24:
                    reasons.append(
                        f"Job at {job.get('company', '?')}: stated duration "
                        f"{dur}mo but dates span ~{actual_months}mo"
                    )

    is_honeypot = len(reasons) >= 2  # need multiple signals to flag
    return is_honeypot, reasons


# ============================================================================
# Master scorer
# ============================================================================

def score_candidate(candidate):
    """
    Score a single candidate. Returns a dict with:
      - total_score: float
      - component_scores: dict of each component's raw score
      - details: dict of detailed breakdowns per component
      - is_honeypot: bool
      - honeypot_reasons: list[str]
    """
    # Run all components
    title_score, title_details = score_title_career(candidate)
    skills_score, skills_details = score_skills(candidate)
    exp_score, exp_details = score_experience(candidate)
    loc_score, loc_details = score_location(candidate)
    edu_score, edu_details = score_education(candidate)
    behavioral_mult, behavioral_details = compute_behavioral_multiplier(candidate)
    is_honeypot, honeypot_reasons = detect_honeypot(candidate)

    # Raw sum of components 1-5
    raw_sum = title_score + skills_score + exp_score + loc_score + edu_score

    # Apply behavioral multiplier
    adjusted = raw_sum * behavioral_mult

    # Apply honeypot penalty
    if is_honeypot:
        total_score = -999.0
    else:
        total_score = round(adjusted, 4)

    return {
        "total_score": total_score,
        "raw_sum": round(raw_sum, 4),
        "behavioral_multiplier": behavioral_mult,
        "component_scores": {
            "title_career": round(title_score, 2),
            "skills": round(skills_score, 2),
            "experience": round(exp_score, 2),
            "location": round(loc_score, 2),
            "education": round(edu_score, 2),
        },
        "details": {
            "title_career": title_details,
            "skills": skills_details,
            "experience": exp_details,
            "location": loc_details,
            "education": edu_details,
            "behavioral": behavioral_details,
        },
        "is_honeypot": is_honeypot,
        "honeypot_reasons": honeypot_reasons,
    }
