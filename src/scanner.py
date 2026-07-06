#!/usr/bin/env python3
"""
UpworkBridge — Job Scanner
==========================
Scans Upwork for matching jobs across configured categories and tiers.
Uses the Upwork GraphQL API (requires OAuth 2.0 credentials).

Setup:
  1. Get API keys from https://www.upwork.com/developer/keys/apply
  2. Copy config.example.py → config.py and fill in credentials
  3. Run: python src/scanner.py --auth   (first-time browser auth)
  4. Run: python src/scanner.py           (subsequent runs use stored token)

Usage:
  python src/scanner.py                     # Search all categories
  python src/scanner.py --tier 1            # Only Tier 1 jobs
  python src/scanner.py --category "AI/ML"  # Specific category
  python src/scanner.py --auth              # Re-authorize OAuth
  python src/scanner.py --cron              # Cron-friendly output
"""

import json
import os
import sys
import time
import hashlib
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Try loading config
sys.path.insert(0, str(Path(__file__).parent))
try:
    from config import (
        UPWORK_CLIENT_ID,
        UPWORK_CLIENT_SECRET,
        UPWORK_REDIRECT_URI,
        TOKEN_FILE,
        JOB_SEARCH_QUERIES,
        SEARCH_INTERVAL_HOURS,
        MAX_JOBS_PER_QUERY,
        MAX_TOTAL_JOBS,
        PREFERRED_COUNTRIES,
        REQUIRE_PAYMENT_VERIFIED,
        MIN_CLIENT_RATING,
        MIN_CLIENT_TOTAL_SPENT,
        EXCLUDED_CATEGORIES,
        SCORING,
        TOP_JOBS_TO_SHOW,
        MIN_SCORE_TO_SHOW,
        FREELANCER,
    )
except ImportError as e:
    print(f"[!] Error loading config.py: {e}")
    print("[!] Copy config.example.py to config.py and fill in your credentials.")
    sys.exit(1)

# ──────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────

GRAPHQL_URL = "https://api.upwork.com/graphql"
AUTH_URL = "https://www.upwork.com/oauth2/token"
AUTHORIZE_URL = "https://www.upwork.com/oauth2/authorize"

try:
    import requests
except ImportError:
    print("[*] Installing required library: requests")
    os.system("pip install requests")
    import requests


def get_stored_token():
    """Load stored OAuth token from file."""
    token_path = Path(TOKEN_FILE).expanduser()
    if token_path.exists():
        try:
            with open(token_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_token(token_data):
    """Save OAuth token to file."""
    token_path = Path(TOKEN_FILE).expanduser()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)
    token_path.chmod(0o600)
    print(f"[+] Token saved to {token_path}")


def check_api_ready():
    """Check if API credentials are configured."""
    if UPWORK_CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("[!] API credentials not configured!")
        print("[!] 1. Go to https://www.upwork.com/developer/keys/apply")
        print("[!] 2. Request an OAuth 2.0 API key")
        print("[!] 3. Update UPWORK_CLIENT_ID and UPWORK_CLIENT_SECRET in config.py")
        print("[!] 4. Run: python src/scanner.py --auth")
        return False
    return True


def do_oauth_auth():
    """Step 1 of OAuth: Generate authorization URL for user to visit."""
    if not check_api_ready():
        return None

    state = hashlib.sha256(os.urandom(32)).hexdigest()[:16]

    params = {
        "response_type": "code",
        "client_id": UPWORK_CLIENT_ID,
        "redirect_uri": UPWORK_REDIRECT_URI,
        "state": state,
        "scope": "openid profile jobs contracts messages",
    }

    auth_url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    print("\n" + "=" * 60)
    print("  OAUTH AUTHORIZATION REQUIRED")
    print("=" * 60)
    print(f"\n  1. Open this URL in your browser:\n")
    print(f"     {auth_url}")
    print(f"\n  2. Log into Upwork and authorize the application")
    print(f"  3. You'll be redirected to {UPWORK_REDIRECT_URI}?code=...")
    print(f"  4. Copy the entire redirect URL and paste it below\n")
    print("=" * 60)

    redirect_response = input("\nPaste the redirect URL here: ").strip()

    parsed = urllib.parse.urlparse(redirect_response)
    code_params = urllib.parse.parse_qs(parsed.query)

    if "code" not in code_params:
        print(f"[!] Could not find authorization code in URL.")
        print(f"[!] Parameters found: {list(code_params.keys())}")
        return None

    auth_code = code_params["code"][0]

    print("[*] Exchanging authorization code for access token...")

    response = requests.post(
        AUTH_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": UPWORK_CLIENT_ID,
            "client_secret": UPWORK_CLIENT_SECRET,
            "code": auth_code,
            "redirect_uri": UPWORK_REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        print(f"[!] Token exchange failed: {response.status_code}")
        print(f"[!] Response: {response.text}")
        return None

    token_data = response.json()
    token_data["acquired_at"] = time.time()
    save_token(token_data)

    print("[+] Authentication successful!")
    print(f"[+] Access token expires in: {token_data.get('expires_in', 'unknown')} seconds")
    print(f"[+] Refresh token obtained: {'Yes' if token_data.get('refresh_token') else 'No'}")
    return token_data


def get_valid_token():
    """Get a valid access token, refreshing if necessary."""
    token_data = get_stored_token()
    if not token_data:
        print("[!] No stored token. Run --auth first.")
        return None

    acquired_at = token_data.get("acquired_at", 0)
    expires_in = token_data.get("expires_in", 3600)
    expires_at = acquired_at + expires_in - 300

    if time.time() < expires_at:
        return token_data.get("access_token")

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        print("[!] Token expired and no refresh token available.")
        print("[!] Run --auth to re-authorize.")
        return None

    print("[*] Token expired, refreshing...")
    response = requests.post(
        AUTH_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": UPWORK_CLIENT_ID,
            "client_secret": UPWORK_CLIENT_SECRET,
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        print(f"[!] Token refresh failed: {response.status_code}")
        print("[!] Run --auth to re-authorize.")
        return None

    new_token = response.json()
    new_token["acquired_at"] = time.time()
    if "refresh_token" not in new_token:
        new_token["refresh_token"] = refresh_token
    save_token(new_token)
    return new_token.get("access_token")


# ──────────────────────────────────────────
# API Query
# ──────────────────────────────────────────


def graphql_query(access_token, query, variables=None):
    """Execute a GraphQL query against the Upwork API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"[!] GraphQL query failed: HTTP {response.status_code}")
        print(f"[!] Response: {response.text[:500]}")
        return None
    result = response.json()
    if "errors" in result:
        print(f"[!] GraphQL errors: {result['errors']}")
        return None
    return result.get("data")


def search_jobs(access_token, query_text, min_budget=0, limit=20):
    """Search for jobs using the Upwork GraphQL API."""
    search_query = """
    query SearchJobs($params: SearchJobParams!) {
        searchJobs(params: $params) {
            items {
                id
                title
                description
                budget { min max type }
                skills
                client {
                    name
                    country
                    paymentVerificationStatus
                    totalSpent
                    rating
                    jobsPosted
                    hireRate
                }
                publishedDate
                proposals { count }
                category
                subcategory
                duration
                workload
                jobType
                isHourly
                experienceLevel
            }
            totalCount
        }
    }
    """
    variables = {"params": {"query": query_text, "limit": limit, "sort": "recency", "unavailable": False}}
    if min_budget > 0:
        variables["params"]["budget"] = {"min": min_budget}
    return graphql_query(access_token, search_query, variables)


# ──────────────────────────────────────────
# Job Filtering & Scoring
# ──────────────────────────────────────────


def score_job(job):
    """Score a job 0-100 based on fit criteria."""
    score = 0
    client = job.get("client") or {}
    if client.get("paymentVerificationStatus") == "VERIFIED":
        score += SCORING.get("payment_verified", 25)
    rating = client.get("rating") or 0
    if rating >= MIN_CLIENT_RATING:
        score += SCORING.get("client_rating_weight", 10) * min(1.0, (rating - 3) / 2)
    budget = job.get("budget") or {}
    budget_max = budget.get("max") or budget.get("min") or 0
    for threshold, bonus in sorted(SCORING.get("budget_tier_bonus", {}).items(), reverse=True):
        if budget_max >= threshold:
            score += bonus
            break
    client_country = client.get("country") or ""
    if client_country in PREFERRED_COUNTRIES:
        score += SCORING.get("country_match", 10)
    published = job.get("publishedDate")
    if published:
        try:
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - pub_date < timedelta(hours=24):
                score += SCORING.get("recent_posting", 15)
        except (ValueError, TypeError):
            pass
    proposals = job.get("proposals") or {}
    proposal_count = proposals.get("count") or 0
    if proposal_count == 0:
        score += SCORING.get("no_proposals_yet", 10)
    elif proposal_count <= 5:
        score += 5
    return min(score, 100)


def filter_jobs(jobs, category):
    """Filter jobs by quality criteria."""
    filtered = []
    skip_reasons = {"excluded_category": 0, "low_budget": 0, "other": 0}
    for job in jobs:
        items = job.get("items") or []
        for item in items:
            cat = item.get("category") or ""
            if any(excl.lower() in cat.lower() for excl in EXCLUDED_CATEGORIES):
                skip_reasons["excluded_category"] += 1
                continue
            item_score = score_job(item)
            if item_score >= MIN_SCORE_TO_SHOW:
                filtered.append({"job": item, "score": item_score, "category": category})
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered, skip_reasons


# ──────────────────────────────────────────
# Output Formatting
# ──────────────────────────────────────────


def format_job_for_display(job_data, index=None):
    """Format a job entry for display."""
    job = job_data["job"]
    score = job_data["score"]
    category = job_data["category"]
    client = job.get("client") or {}
    budget = job.get("budget") or {}
    proposals = job.get("proposals") or {}

    title = job.get("title", "Untitled")
    job_id = job.get("id", "")
    description = job.get("description", "")[:300]
    if len(job.get("description", "")) > 300:
        description += "..."

    budget_min = budget.get("min")
    budget_max = budget.get("max")
    budget_type = budget.get("type", "")
    if budget_min and budget_max:
        budget_str = f"${budget_min:,.0f} - ${budget_max:,.0f}"
    elif budget_min:
        budget_str = f"${budget_min:,.0f}+"
    else:
        budget_str = "Not specified"
    if budget_type:
        budget_str += f" ({budget_type})"

    stars = "⭐" * min(5, max(1, round(score / 20)))
    client_name = (client.get("name") or "Anonymous")[:20]
    client_country = client.get("country") or "Unknown"
    client_rating = client.get("rating") or "N/A"
    proposal_count = proposals.get("count") or "?"

    formatted = (
        f"{'📌 ' if index else ''}**{title}**\n"
        f"├  💰 **Score:** {score}/100 {stars}\n"
        f"├  📂 **Category:** {category}\n"
        f"├  💵 **Budget:** {budget_str}\n"
        f"├  🏢 **Client:** {client_name} ({client_country})"
    )
    if client_rating != "N/A":
        formatted += f" — ⭐ {client_rating}"
    formatted += "\n"
    formatted += (
        f"├  📋 **Proposals:** {proposal_count}\n"
        f"├  📝 {description}\n"
        f"└  🔗 upwork.com/jobs/~{job_id}\n"
    )
    return formatted


def format_summary(stats):
    """Format a run summary."""
    total_found = stats.get("total_found", 0)
    total_qualified = stats.get("total_qualified", 0)
    categories = stats.get("categories", {})

    summary = [
        f"**📊 Scan Summary**",
        f"├  🔍 **Queries:** {stats.get('queries_run', 0)}",
        f"├  📥 **Jobs Found:** {total_found}",
        f"├  ✅ **Qualified:** {total_qualified}",
        f"└  **By Tier:**",
    ]
    for tier in ["Tier 1", "Tier 2", "Tier 3"]:
        count = categories.get(tier, 0)
        if count > 0:
            summary.append(f"    {'├' if tier != 'Tier 3' else '└'}  {tier}: {count} jobs")
    return "\n".join(summary)


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="UpworkBridge — Smart Job Scanner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Only search a specific tier")
    parser.add_argument("--category", type=str, help="Only search a specific category")
    parser.add_argument("--auth", action="store_true", help="Run OAuth authorization flow")
    parser.add_argument("--cron", action="store_true", help="Cron-friendly output (JSON)")

    args = parser.parse_args()

    if args.auth:
        do_oauth_auth()
        return

    # Get access token
    access_token = get_valid_token()
    if not access_token:
        return

    # Filter queries
    queries = JOB_SEARCH_QUERIES
    if args.tier:
        queries = [q for q in queries if q["tier"] == args.tier]
    if args.category:
        queries = [q for q in queries if args.category.lower() in q["category"].lower()]

    if not queries:
        print("[!] No matching queries found.")
        return

    print(f"\n[*] UpworkBridge Scanner — Running {len(queries)} queries...\n")

    all_results = {}
    stats = {
        "queries_run": 0,
        "total_found": 0,
        "total_qualified": 0,
        "skipped": {"excluded_category": 0, "low_budget": 0, "other": 0},
        "categories": {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0},
    }

    for query_config in queries:
        if args.cron:
            print(f"    Query: {query_config['query']} ({query_config['category']})", end="... ")
        else:
            print(f"\n{'─' * 50}")
            print(f"  📂 {query_config['category']} [Tier {query_config['tier']}]")
            print(f"  🔍 \"{query_config['query']}\"")

        result = search_jobs(access_token, query_config["query"], query_config.get("min_budget", 0), MAX_JOBS_PER_QUERY)
        stats["queries_run"] += 1

        if result and "searchJobs" in result:
            jobs_data = result["searchJobs"]
            items = jobs_data.get("items") or []
            stats["total_found"] += len(items)
            filtered, skip_reasons = filter_jobs([jobs_data], query_config["category"])
            for k, v in skip_reasons.items():
                stats["skipped"][k] += v

            tier_key = f"Tier {query_config['tier']}"
            if filtered:
                stats["categories"][tier_key] = stats["categories"].get(tier_key, 0) + len(filtered)
                stats["total_qualified"] += len(filtered)

                if query_config["category"] not in all_results:
                    all_results[query_config["category"]] = []
                all_results[query_config["category"]].extend(filtered[:MAX_JOBS_PER_QUERY])

            if args.cron:
                print(f"{len(filtered)} qualified")
            else:
                print(f"  → {len(filtered)} qualified jobs")
                if not filtered:
                    print(f"     (no matching jobs above minimum score)")
        else:
            if args.cron:
                print("no results")

    # Display results
    if args.cron:
        output = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "jobs": {},
        }
        for category, jobs in all_results.items():
            sorted_jobs = sorted(jobs, key=lambda x: x["score"], reverse=True)[:TOP_JOBS_TO_SHOW]
            output["jobs"][category] = [
                {
                    "id": j["job"].get("id"),
                    "title": j["job"].get("title"),
                    "url": f"https://www.upwork.com/jobs/~{j['job'].get('id')}",
                    "score": j["score"],
                    "budget": str(j["job"].get("budget", {})),
                    "client": j["job"].get("client", {}).get("name", "Anonymous"),
                }
                for j in sorted_jobs
            ]
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'=' * 55}")
        print(f"  📊 SCAN RESULTS")
        print(f"{'=' * 55}")
        print(f"\n{format_summary(stats)}\n")

        category_order = sorted(all_results.keys())
        for cat in category_order:
            jobs = sorted(all_results[cat], key=lambda x: x["score"], reverse=True)
            print(f"\n{'─' * 50}")
            print(f"  📂 {cat} ({len(jobs)} qualified)")
            print(f"{'─' * 50}")
            for i, job_data in enumerate(jobs[:TOP_JOBS_TO_SHOW], 1):
                print(f"\n{format_job_for_display(job_data, i)}")

        print(f"\n{'=' * 55}")
        print(f"  To generate a proposal: python src/propose.py --job-id <JOB_ID>")
        print(f"{'=' * 55}")


if __name__ == "__main__":
    main()