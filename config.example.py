"""UpworkBridge Configuration Example

Copy this to config.py and fill in your credentials:
    cp config.example.py config.py
    nano config.py
"""

# ═══════════════════════════════════════════
# API CREDENTIALS — Fill these in after receiving from Upwork
# ═══════════════════════════════════════════

UPWORK_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
UPWORK_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
UPWORK_REDIRECT_URI = "http://localhost:8080/callback"

# Token storage path (stores refresh token after first auth)
TOKEN_FILE = "~/.upworkbridge_token.json"

# ═══════════════════════════════════════════
# SEARCH CONFIGURATION
# ═══════════════════════════════════════════

SEARCH_INTERVAL_HOURS = 2
MAX_JOBS_PER_QUERY = 20
MAX_TOTAL_JOBS = 30

# ═══════════════════════════════════════════
# JOB SEARCH QUERIES — Organized by category
# ═══════════════════════════════════════════

JOB_SEARCH_QUERIES = [
    # Tier 1: AI/ML (highest priority)
    {"category": "AI/ML Implementation", "tier": 1, "query": "AI agent development", "min_budget": 500},
    {"category": "AI/ML Implementation", "tier": 1, "query": "LLM fine-tuning", "min_budget": 500},
    {"category": "AI/ML Implementation", "tier": 1, "query": "RAG pipeline", "min_budget": 500},
    {"category": "AI/ML Implementation", "tier": 1, "query": "AI automation workflow", "min_budget": 500},
    {"category": "AI/ML Implementation", "tier": 1, "query": "AI implementation consultant", "min_budget": 500},
    # Tier 1b: Government/Defense
    {"category": "Government IT", "tier": 1, "query": "TS/SCI clearance data analysis", "min_budget": 500},
    {"category": "Government IT", "tier": 1, "query": "defense contractor data analyst", "min_budget": 500},
    # Tier 2: Data & Automation
    {"category": "Data Analysis", "tier": 2, "query": "Python data analysis", "min_budget": 200},
    {"category": "Data Analysis", "tier": 2, "query": "Power BI dashboard", "min_budget": 200},
    {"category": "Data Analysis", "tier": 2, "query": "SQL data analyst", "min_budget": 200},
    {"category": "Process Automation", "tier": 2, "query": "Power Automate workflow", "min_budget": 200},
    {"category": "Process Automation", "tier": 2, "query": "business process automation", "min_budget": 200},
    {"category": "Process Automation", "tier": 2, "query": "Telegram bot development", "min_budget": 200},
    {"category": "Technical Writing", "tier": 2, "query": "technical writer SOP documentation", "min_budget": 100},
    {"category": "Technical Writing", "tier": 2, "query": "AI documentation specialist", "min_budget": 200},
    # Tier 3: Supplementary
    {"category": "Language Services", "tier": 3, "query": "Pashto translator", "min_budget": 50},
    {"category": "Language Services", "tier": 3, "query": "Spanish translator", "min_budget": 50},
    {"category": "Virtual Assistant", "tier": 3, "query": "AI virtual assistant", "min_budget": 100},
    {"category": "Systems Admin", "tier": 3, "query": "Linux system administration", "min_budget": 100},
    {"category": "Systems Admin", "tier": 3, "query": "Docker container setup", "min_budget": 100},
    {"category": "Real Estate", "tier": 3, "query": "real estate financial analysis", "min_budget": 100},
    {"category": "Training", "tier": 3, "query": "AI training consultant", "min_budget": 200},
]

# ═══════════════════════════════════════════
# FILTERING RULES
# ═══════════════════════════════════════════

PREFERRED_COUNTRIES = ["United States", "Canada", "United Kingdom", "Australia"]
REQUIRE_PAYMENT_VERIFIED = True
MIN_CLIENT_RATING = 4.0
MIN_CLIENT_TOTAL_SPENT = 100

EXCLUDED_CATEGORIES = [
    "Web Development",
    "Mobile Development",
    "Video Production",
    "Writing (General)",
    "Customer Service",
    "Data Entry",
]

# ═══════════════════════════════════════════
# SCORING WEIGHTS
# ═══════════════════════════════════════════

SCORING = {
    "payment_verified": 25,
    "client_rating_weight": 10,
    "budget_tier_bonus": {5000: 30, 2000: 20, 1000: 10, 500: 5},
    "country_match": 10,
    "recent_posting": 15,
    "no_proposals_yet": 10,
}

# ═══════════════════════════════════════════
# NOTIFICATION
# ═══════════════════════════════════════════

TOP_JOBS_TO_SHOW = 5
MIN_SCORE_TO_SHOW = 30

# ═══════════════════════════════════════════
# FREELANCER PROFILE (for proposal generation)
# ═══════════════════════════════════════════

FREELANCER = {
    "name": "Your Name",
    "title": "AI Implementation Consultant & Automation Specialist",
    "current_role": "Your Current Role",
    "background": "Your professional background",
    "clearance": "Your clearance if applicable",
    "certifications": ["Certification 1", "Certification 2"],
    "core_skills": [
        "AI Agent Development",
        "Python",
        "SQL",
        "Power BI",
        "Process Automation",
        "Linux/Docker/PostgreSQL",
    ],
    "languages": ["English (Native)"],
    "location": "Your Location",
    "rate_range": "$50-$150/hr depending on scope",
    "portfolio": [
        {"name": "Project Name", "description": "Brief description of project"},
    ],
    "agent_note": "Optional note about how you work",
}