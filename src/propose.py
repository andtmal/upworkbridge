#!/usr/bin/env python3
"""
UpworkBridge — Proposal Generator
==================================
Generates tailored Upwork proposals based on job descriptions
and the freelancer's skills/portfolio.

Usage:
  python src/propose.py --job-id JOB_ID      # Fetch job via API + generate proposal
  python src/propose.py --url JOB_URL        # Use a job URL
  python src/propose.py --describe "..."     # Paste a job description manually
  python src/propose.py --template           # Show the base template
  python src/propose.py --list-skills        # Show configured skills/experience
"""

import json
import os
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
try:
    from config import FREELANCER, GRAPHQL_URL, TOKEN_FILE
except ImportError as e:
    print(f"[!] Error loading config.py: {e}")
    print("[!] Copy config.example.py to config.py and fill in your profile.")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[*] Installing required library: requests")
    os.system("pip install requests")
    import requests

# ═══════════════════════════════════════════
# PROPOSAL BEST PRACTICES (built-in)
# ═══════════════════════════════════════════

BEST_PRACTICES = """
## Upwork Proposal Best Practices

### Structure
1. **First 2 lines are critical** — clients decide in 5 seconds
2. **Address the client by name** if visible
3. **Show you read the full job description** — reference specific details
4. **Be concise** — 150-300 words is ideal
5. **End with a question** — invites response

### What Works (Data from 150k+ proposals)
✅ Relevant attachments increase response rate by 40% (8.2% → 11.5%)
✅ Personalized first line increases views by 2.5x
✅ Asking 1-2 smart questions shows genuine interest
✅ Mentioning specific tools/technologies from the job description

### What Doesn't Work
❌ Generic copy-paste proposals (instant rejection)
❌ Over-promising (AI-generated hype)
❌ Talking about yourself without connecting to their problem
❌ Wall of text (no paragraph breaks)

### Rate Psychology
- If you're new to Upwork: start 10-20% below target to land first clients
- After 5+ jobs with good feedback: raise to target rate
- Fixed-price: break into milestones ($500-$2k per milestone)
"""

# ═══════════════════════════════════════════
# TEMPLATE SYSTEM
# ═══════════════════════════════════════════

BASE_TEMPLATE = """Hi {client_name},

I read your project — {job_title_short} — and it matches exactly the kind of work I do as an AI Implementation Consultant.

{opening_relevance}

{body_experience}

{body_solution}

A quick question: {question}

I'm available to start immediately and work in your time zone. Would you be open to a brief call to discuss how I can help?

Best,
{FREELANCER_NAME}"""

TIER_TEMPLATES = {
    "AI/ML": {
        "opening": (
            "I specialize in building AI agents and automation systems for businesses "
            "that want to streamline operations. My current work involves production "
            "AI agent infrastructure (agent frameworks, RAG pipelines, Telegram bots) "
            "for receipt processing, expense categorization, and automated workflows."
        ),
        "body": (
            "My background includes:\n"
            "• Building custom AI agents using agent frameworks\n"
            "• RAG pipeline development for document intelligence\n"
            "• Python automation, PostgreSQL, and API integration\n"
            "• Production VPS infrastructure (Docker, Linux, CI/CD)"
        ),
        "question": "What's the primary data source or workflow you're looking to automate?",
    },
    "Data": {
        "opening": (
            "I'm an experienced Data Analyst who builds automation tools on the side. "
            "I work with SQL, Python, Power BI, and end-to-end data pipeline design."
        ),
        "body": (
            "My relevant experience:\n"
            "• Data analysis with SQL, Python (pandas, numpy), and Power BI\n"
            "• Building automated dashboards and reporting pipelines\n"
            "• Workflow automation design\n"
            "• Data cleaning, transformation, and visualization"
        ),
        "question": "What format is the source data in, and what's the key metric you want to track?",
    },
    "Automation": {
        "opening": (
            "I build automation systems that eliminate manual busywork. "
            "My projects include AI-powered bots that automatically "
            "categorizes data, tracks entities, and stores results."
        ),
        "body": (
            "My automation toolkit:\n"
            "• Python scripting for process automation\n"
            "• Workflow automation tools\n"
            "• Chat bot development with webhook integration\n"
            "• Linux cron/scheduled task automation\n"
            "• Docker/PostgreSQL deployment"
        ),
        "question": "What's the most time-consuming manual process in your current workflow?",
    },
    "Government": {
        "opening": (
            "I'm one of the few freelancers on Upwork with an active clearance "
            "and direct experience in defense intelligence operations. "
            "I understand what secure, compliant work looks like."
        ),
        "body": (
            "My cleared background:\n"
            f"{'• Active clearance (current)' if FREELANCER.get('clearance') else '• Government contracting experience'}\n"
            "• 10 years military intelligence experience\n"
            "• CompTIA Security+ (DoD 8570 compliant)\n"
            "• Data analysis for government systems"
        ),
        "question": "Does this work require the contractor to hold an active clearance, or just the ability to handle sensitive data?",
    },
    "Language": {
        "opening": (
            "I'm a DLI graduate in Pashto (3/2+/2) with 10 years of intelligence experience. "
            "I also speak fluent Spanish."
        ),
        "body": (
            "My language qualifications:\n"
            "• DLI Pashto course graduate (64 weeks)\n"
            "• 10 years using language skills in operational intelligence\n"
            "• Spanish: fluent\n"
            "• Military cryptologic language analyst background"
        ),
        "question": "What's the time frame and expected volume?",
    },
    "Default": {
        "opening": (
            "I'm a US-based AI Implementation Consultant and Data Analyst with "
            "experience building systems that solve real business problems. "
            "I deliver working solutions — not just plans and proposals."
        ),
        "body": (
            "What I bring:\n"
            "• Python, SQL, Power BI, automation engineering\n"
            "• Production infrastructure (Linux, Docker, PostgreSQL)\n"
            f"{'• ' + FREELANCER.get('clearance', 'Reliable, responsive communication') + ' environment' if FREELANCER.get('clearance') else '• Reliable, responsive communication'}\n"
            "• An AI agent ecosystem that multiplies delivery speed"
        ),
        "question": "What does success look like for this project — what's the one thing you need to see working?",
    },
}


def detect_job_category(title, description):
    """Detect the job category for template selection."""
    text = (title + " " + description).lower()

    if any(w in text for w in ["ai", "llm", "rag", "agent", "machine learning", "gpt", "claude", "openai", "fine-tun"]):
        return "AI/ML"
    if any(w in text for w in ["clearance", "ts/sci", "classified", "government", "defense", "security clearance"]):
        return "Government"
    if any(w in text for w in ["automation", "workflow", "bot", "telegram", "power automate"]):
        return "Automation"
    if any(w in text for w in ["data analysis", "sql", "dashboard", "power bi", "analytics", "etl", "data pipeline"]):
        return "Data"
    if any(w in text for w in ["pashto", "translation", "interpreter", "spanish", "translator"]):
        return "Language"

    return "Default"


# ═══════════════════════════════════════════
# AI-POWERED PROPOSAL GENERATION
# ═══════════════════════════════════════════

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_with_ai(job_title, job_description, client_name, category):
    """Use the configured AI model to generate a tailored proposal."""
    system_prompt = f"""You are a professional proposal writer for Upwork freelancer {FREELANCER.get('name', 'the user')}.

FREELANCER BIO:
- Name: {FREELANCER.get('name', 'Freelancer Name')}
- Title: {FREELANCER.get('title', 'Title')}
- Current role: {FREELANCER.get('current_role', 'Current Role')}
- Background: {FREELANCER.get('background', 'Background')}
- Clearance: {FREELANCER.get('clearance', 'N/A')}
- Location: {FREELANCER.get('location', 'Location')}
- Languages: {', '.join(FREELANCER.get('languages', ['English']))}
- Certifications: {', '.join(FREELANCER.get('certifications', []))}
- Core skills: {', '.join(FREELANCER.get('core_skills', []))}

WRITING STYLE:
- Professional but conversational
- Specific, not generic
- Show you understand their problem
- Reference relevant experience
- Keep to 150-250 words
- End with a question

RULES:
- Address the client's specific job requirements
- Don't overpromise
- Be honest about availability
- Keep tone confident but not arrogant
- No markdown formatting in the proposal itself"""

    user_prompt = f"""Generate a tailored Upwork proposal for this job:

CLIENT NAME: {client_name}
JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_description[:2000]}

CATEGORY: {category}

Write a proposal following the guidelines above."""

    if OPENROUTER_KEY:
        try:
            response = requests.post(
                OPENROUTER_URL,
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500,
                },
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/upworkbridge/upworkbridge",
                },
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"[!] AI call failed (HTTP {response.status_code}), using template...")
        except Exception as e:
            print(f"[!] AI call error: {e}, using template...")

    return None


# ═══════════════════════════════════════════
# TEMPLATE-BASED GENERATION
# ═══════════════════════════════════════════


def generate_template_proposal(job_title, job_description, client_name="there", category=None):
    """Generate a proposal using templates."""
    if not category:
        category = detect_job_category(job_title, job_description)

    templates = TIER_TEMPLATES.get(category, TIER_TEMPLATES["Default"])

    if len(job_title) > 40:
        job_title_short = job_title[:37] + "..."
    else:
        job_title_short = job_title

    proposal = BASE_TEMPLATE.format(
        client_name=client_name or "there",
        job_title_short=job_title_short,
        opening_relevance=templates["opening"],
        body_experience=templates["body"],
        question=templates["question"],
        body_solution="I'd approach this by first understanding your current workflow, "
                      "then designing a solution that fits your specific tools and constraints.",
        FREELANCER_NAME=FREELANCER.get("name", "Your Name"),
    )
    return proposal


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="UpworkBridge — Proposal Generator"
    )
    parser.add_argument("--job-id", type=str, help="Upwork job ID to fetch details for")
    parser.add_argument("--url", type=str, help="Upwork job URL")
    parser.add_argument("--describe", type=str, help="Paste job description text directly")
    parser.add_argument("--title", type=str, help="Job title (used with --describe)")
    parser.add_argument("--client", type=str, default="there", help="Client name")
    parser.add_argument("--template", action="store_true", help="Show the base template")
    parser.add_argument("--ai", action="store_true", help="Use AI generation (requires OPENROUTER_API_KEY env)")
    parser.add_argument("--list-skills", action="store_true", help="Show configured skills/experience")
    parser.add_argument("--best-practices", action="store_true", help="Show proposal best practices")

    args = parser.parse_args()

    if args.template:
        print("\n" + "=" * 60)
        print("  BASE PROPOSAL TEMPLATE")
        print("=" * 60)
        print(BASE_TEMPLATE)
        print("\nTier-specific templates available:")
        for tier in TIER_TEMPLATES:
            print(f"  - {tier}")
        return

    if args.list_skills:
        print("\n" + "=" * 60)
        print("  FREELANCER SKILLS & EXPERIENCE")
        print("=" * 60)
        print(f"\nName: {FREELANCER.get('name', 'Not configured')}")
        print(f"Title: {FREELANCER.get('title', 'Not configured')}")
        print(f"Current: {FREELANCER.get('current_role', 'Not configured')}")
        print(f"Background: {FREELANCER.get('background', 'Not configured')}")
        if FREELANCER.get("clearance"):
            print(f"Clearance: {FREELANCER['clearance']}")
        print(f"\nCertifications:")
        for cert in FREELANCER.get("certifications", []):
            print(f"  - {cert}")
        print(f"\nCore Skills:")
        for skill in FREELANCER.get("core_skills", []):
            print(f"  - {skill}")
        print(f"\nLanguages:")
        for lang in FREELANCER.get("languages", []):
            print(f"  - {lang}")
        print(f"\nRate Range: {FREELANCER.get('rate_range', 'Not configured')}")
        print(f"\nPortfolio:")
        for p in FREELANCER.get("portfolio", []):
            print(f"  - {p['name']}: {p['description']}")
        return

    if args.best_practices:
        print(BEST_PRACTICES)
        return

    # Generate proposal
    job_title = "Untitled Project"
    job_description = ""
    client_name = args.client

    if args.describe:
        job_description = args.describe
        job_title = args.title or "Custom Project"

    elif args.job_id:
        print(f"[*] Job ID provided: {args.job_id}")
        print("[*] Will fetch via API once credentials are active.")
        print("[*] For now, use --describe to paste the job description.\n")
        return

    elif args.url:
        print(f"[*] URL provided: {args.url}")
        print("[*] For now, use --describe to paste the job description.\n")
        return

    if not job_description:
        parser.print_help()
        print("\n[!] Provide job details via --describe, --job-id, or --url")
        return

    category = detect_job_category(job_title, job_description)
    print(f"[*] Detected category: {category}")

    proposal = None
    if args.ai:
        print("[*] Generating with AI...")
        proposal = generate_with_ai(job_title, job_description, client_name, category)

    if not proposal:
        print("[*] Using template-based generation...")
        proposal = generate_template_proposal(job_title, job_description, client_name, category)

    print("\n" + "=" * 60)
    print(f"  PROPOSAL DRAFT — {job_title[:40]}")
    print("=" * 60 + "\n")
    print(proposal)

    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print(f"  1. Copy this proposal text")
    print(f"  2. Go to: https://www.upwork.com")
    print(f"  3. Navigate to the job listing")
    print(f"  4. Click 'Submit a Proposal'")
    print(f"  5. Paste and personalize as needed")
    print(f"\n  💡 Tip: Attach a relevant portfolio piece")
    print(f"  💡 Tip: Keep Connects cost in mind (varies by job)")
    print("=" * 60)

    output_dir = Path.home() / ".upwork_proposals"
    output_dir.mkdir(exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c == " " else "_" for c in job_title)[:40]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}.md"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        f.write(f"# Proposal: {job_title}\n")
        f.write(f"# Client: {client_name}\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# Category: {category}\n\n")
        f.write(proposal)
    print(f"\n[+] Saved to: {filepath}")


if __name__ == "__main__":
    main()