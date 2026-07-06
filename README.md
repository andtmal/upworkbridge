# UpworkBridge — MCP Server for Upwork

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects AI coding assistants and agentic workflows to the Upwork freelance marketplace. Enables AI-powered job discovery, proposal generation, and contract management through a structured tool interface.

## Overview

UpworkBridge exposes Upwork's platform capabilities as MCP tools, allowing AI agents to:

- **Search jobs** across 25+ skill categories with configurable scoring and filtering
- **Generate tailored proposals** using freelancer profile data and job-specific context
- **Manage contracts and messages** (proposed — requires OAuth scope)
- **Monitor activity** via a cron-enabled scanning pipeline

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AI Assistant (Host)                  │
│  (Claude Code, Cursor, Copilot, Hermes Agent, etc.) │
└────────────────────┬────────────────────────────────┘
                     │ MCP Protocol (stdio/SSE)
                     ▼
┌─────────────────────────────────────────────────────┐
│                  UpworkBridge Server                  │
│                                                       │
│  ┌──────────────┐    ┌───────────────────────────┐   │
│  │  Scanner     │ →  │  Job Search & Scoring     │   │
│  │  Module      │    │  - 25+ predefined queries │   │
│  └──────────────┘    │  - Multi-tier categories  │   │
│                      │  - Smart scoring engine   │   │
│  ┌──────────────┐    └───────────────────────────┘   │
│  │  Proposer    │    ┌───────────────────────────┐   │
│  │  Module      │ →  │  Proposal Generation      │   │
│  └──────────────┘    │  - AI-assisted drafting   │   │
│                      │  - Skill-based templates  │   │
│                      │  - Best practices engine  │   │
│  ┌──────────────┐    └───────────────────────────┘   │
│  │  OAuth       │    ┌───────────────────────────┐   │
│  │  Handler     │ →  │  Token Management         │   │
│  └──────────────┘    │  - OAuth 2.0 auth flow    │   │
│                      │  - Auto token refresh     │   │
│  ┌──────────────┐    └───────────────────────────┘   │
│  │  Config      │    ┌───────────────────────────┐   │
│  │  Engine      │ →  │  Search params, scoring   │   │
│  └──────────────┘    │  weights, user profile    │   │
│                      └───────────────────────────┘   │
└────────────────────┬────────────────────────────────┘
                     │ Upwork API (OAuth 2.0)
                     ▼
┌─────────────────────────────────────────────────────┐
│                  Upwork Platform                      │
│  Job listings · Proposals · Contracts · Messages     │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Upwork API credentials (OAuth 2.0 — [apply here](https://www.upwork.com/developer/keys/apply))

### Installation

```bash
# Clone the repo
git clone https://github.com/your-org/upworkbridge.git
cd upworkbridge

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp config.example.py config.py
# Edit config.py with your Upwork Client ID and Secret

# Run initial OAuth authorization
python src/scanner.py --auth

# Search for jobs
python src/scanner.py

# Generate a proposal
python src/propose.py --job-id <JOB_ID>
```

### MCP Integration

To connect UpworkBridge to an MCP-compatible AI assistant:

```json
{
  "mcpServers": {
    "upwork": {
      "command": "python",
      "args": ["/path/to/upworkbridge/src/scanner.py", "--mcp"],
      "env": {
        "UPWORK_CLIENT_ID": "your_client_id",
        "UPWORK_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

## Features

### 🔍 Job Scanner

Searches Upwork across 10 categories organized in 3 tiers:

| Tier | Category | Target Rate | Query Volume |
|------|----------|-------------|-------------|
| **1** | AI/ML Implementation | $85–$175/hr | 5 queries |
| **1** | Government/Defense IT | $100–$250/hr | 2 queries |
| **2** | Data Analysis | $40–$80/hr | 3 queries |
| **2** | Process Automation | $50–$100/hr | 3 queries |
| **2** | Technical Writing | $40–$80/hr | 2 queries |
| **3** | Language Services | $35–$55/hr | 2 queries |
| **3** | Systems Admin | $35–$65/hr | 2 queries |
| **3** | Virtual Assistant | $20–$45/hr | 1 query |
| **3** | Real Estate | $30–$60/hr | 1 query |
| **3** | AI Training | $40–$80/hr | 1 query |

### 📊 Smart Scoring

Jobs are scored 0–100 based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Payment Verified | 25 pts | Client must have verified payment |
| Client Rating | 10× | Multiplied by (rating - 3) / 2 |
| Budget | 5–30 pts | Scaled by project value |
| Region | 10 pts | US/CA/UK/AU preference |
| Freshness | 15 pts | Posted within 24 hours |
| Competition | 5–10 pts | Fewer proposals = higher score |

### 📝 Proposal Generator

AI-assisted proposal drafting with:
- Job-specific context analysis
- Freelancer profile integration
- Skill-based template matching
- Best-practices checklist
- Dry-run mode for review before submission

## Configuration

All configuration lives in `config.py`:

- **API Credentials** — OAuth 2.0 client ID and secret
- **Search Queries** — Customizable per category
- **Scoring Weights** — Adjustable preference factors
- **Filtering Rules** — Minimum client rating, budget thresholds, country preferences
- **Freelancer Profile** — Skills, certifications, portfolio, rate range

## Roadmap

- [x] Job scanning with multi-query search
- [x] AI-assisted proposal generation
- [x] OAuth 2.0 token management
- [ ] MCP server mode (stdio transport)
- [ ] Proposal submission & tracking
- [ ] Message monitoring
- [ ] Contract status tracking
- [ ] Docker deployment
- [ ] Pre-built GitHub Action for cron scanning

## License

MIT — see `LICENSE`.