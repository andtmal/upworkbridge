# UpworkBridge — API Key Application

**Project Name:** UpworkBridge
**Type:** MCP Server (Model Context Protocol) — Open Source Developer Tool

## Application Summary

UpworkBridge is an open-source **MCP Server** that bridges AI development assistants (Claude Code, Cursor, Copilot, agentic frameworks) to the Upwork marketplace. It enables AI-assisted job discovery and proposal generation through a structured tool interface.

### What it does

1. **Job Discovery & Scoring** — Searches Upwork across 25+ skill categories with a multi-tier query engine. Jobs are scored 0-100 based on client reputation, budget, age, competition, and country preference — helping freelancers focus on high-fit opportunities.

2. **AI-Assisted Proposal Generation** — Analyzes job descriptions against the freelancer's skills and generates tailored proposals using either AI (configurable) or template-based generation with category-specific content (AI/ML, Data, Automation, Government, Language).

3. **Planned: MCP Server Mode** — Exposes search and proposal capabilities as MCP tools so AI coding assistants can interact with Upwork programmatically (stdio transport).

### Why Upwork should approve this key

| Consideration | Detail |
|---------------|--------|
| **Open Source** | Public GitHub repo — full transparency on how the API is used |
| **OAuth 2.0** | Uses standard OAuth 2.0 PKCE flow — per-user, consent-driven |
| **Read-Heavy** | Primary use: job search (read-only queries). Proposal generation is AI-assisted *drafting* — proposals are reviewed and submitted manually by the user |
| **Rate-Limited** | Respects Upwork's rate limits — configurable scan intervals (default 2h) |
| **No Automation Abuse** | Does NOT auto-submit proposals, spam listings, or scrape without auth |
| **Developer Tooling** | Serves the MCP ecosystem — a growing standard for connecting AI tools to APIs |

### OAuth Configuration

- **Redirect URI:** `http://localhost:8080/callback`
- **Scopes Requested:** `openid profile jobs contracts messages`
- **Auth Flow:** Authorization code grant with PKCE

### GitHub Repository

**URL:** `https://github.com/upworkbridge/upworkbridge` *(repository will be created upon API key approval)*

### Technical Details

- **Language:** Python 3.10+
- **Auth:** OAuth 2.0 (Bearer token with refresh)
- **API:** Upwork GraphQL API
- **Transport:** CLI / planned MCP stdio
- **Scope:** Job search, proposal drafting, contract status

### Use Case Statement

> "UpworkBridge is a developer tool that makes Upwork more accessible to the growing ecosystem of AI-assisted developers. By wrapping Upwork's API as MCP tools, we help freelancers discover relevant opportunities faster and draft better, more tailored proposals. This isn't a bot farm or automation spam tool — every proposal is reviewed and submitted by a human. The OAuth 2.0 flow ensures each user authorizes their own account, and the open-source codebase guarantees transparency."

---

**Submitted by:** UpworkBridge Team
**Contact:** GitHub Issues (public repo)