# 🗞️ AI & Tech Weekly — Automated News Digest

A LangGraph-orchestrated pipeline that researches, filters, ranks, and
summarizes the week's most important AI and technology developments, and
publishes a formatted newsletter every Monday morning — built entirely on
free-tier tools and services.

---

## What it does

Every Monday at 07:00 UTC, a GitHub Actions workflow runs a LangGraph
`StateGraph` that:

1. **Collects**, in parallel, from five independent sources covering the
   past 7 days:
   - 8 major tech/security RSS feeds
   - Hacker News (Algolia public API), filtered to high-point posts
   - arXiv (public API), across AI/NLP/ML/robotics/security categories
   - GitHub Search API, for repos gaining real traction in the last week
   - **Tavily** — a search API purpose-built for LLM agents, run against a
     fixed set of topic queries (model releases, dev tools, security,
     robotics, funding)
2. **Deep-scrapes** a small, capped set of the most promising results with
   **Firecrawl**, converting full pages to clean Markdown so the LLM
   summarizes from complete articles, not just snippets, on the items that
   matter most.
3. **Filters, ranks, and formats** everything with an LLM (Groq, via
   LangChain), applying a strict "less news, more signal" rule.
4. **Publishes** the result by committing a new dated Markdown file back to
   the repo automatically.

## Architecture

```
                              START
                                |
      ------------------------------------------------------
      |            |             |              |          |
 collect_rss   collect_hn   collect_arxiv  collect_github  search_tavily
      |            |             |              |          |
      ------------------------------------------------------
                                |
                    enrich_with_firecrawl
                                |
                      format_newsletter  (LLM)
                                |
                               END
```

The five source nodes have no dependency on each other, so LangGraph runs
them concurrently. `enrich_with_firecrawl` is a join — it only fires once
every source node has finished and merged into the shared state — then a
single LLM call filters/ranks/formats the result.

## Why LangGraph, Tavily, and Firecrawl specifically

- **LangGraph** models this as an explicit graph rather than a linear
  script: typed shared state with merge rules (not manual list-appending),
  real parallel fan-out for the five independent sources, and a join point
  before the LLM step — the same primitives used for production agentic
  pipelines, just applied to a scheduled batch job.
- **Tavily** over a generic scraper for search: it's built for LLM
  consumption specifically — structured JSON results instead of raw HTML —
  with a free tier (1,000 searches/month) that comfortably covers one
  weekly run.
- **Firecrawl**, not Tavily, for full-page reads: search and deep-read are
  different jobs. Firecrawl handles JS-rendered pages and returns clean
  Markdown, so it's reserved for the handful of items worth reading in full
  rather than used for search itself. Free tier: ~1,000 credits/month; this
  pipeline caps usage at 5 pages/run to stay well inside it.

## Tech stack

- **Python 3.11**, managed with **`uv`** — lockfile-based reproducible
  installs, no `pip`/`venv` boilerplate
- **LangGraph** — pipeline orchestration (`StateGraph`, parallel fan-out,
  typed reducers)
- **LangChain** (`langchain-groq`, `langchain-tavily`) — LLM and tool
  abstractions
- **Firecrawl** (`firecrawl-py`) — deep page scraping
- **REST APIs** — Hacker News (Algolia), arXiv, GitHub Search
- **GitHub Actions** — cron scheduling, CI/CD, automated commits

## Why I built this

I wanted a weekly signal on AI/tech developments without manually trawling
a dozen sites every Monday — and a chance to build a real, non-trivial
LangGraph pipeline rather than a toy example: multiple concurrent tool
integrations, a join node, and working within a live LLM provider's
rate-limit constraints, end to end, for $0/month.

## Setup

1. **Clone this repo**, then install dependencies with `uv`:
   ```bash
   uv sync
   ```
2. Get three free API keys (no credit card required for any):
   - [Groq](https://console.groq.com) → API Keys → Create API key
   - [Tavily](https://app.tavily.com) → key shown on dashboard after signup
   - [Firecrawl](https://firecrawl.dev) → Dashboard → API Keys
3. Copy `.env.example` to `.env` and fill in the three keys:
   ```bash
   cp .env.example .env
   ```
4. Run it locally:
   ```bash
   uv run main.py
   ```
5. For the automated weekly run, add the same three keys as **repository
   secrets** (Settings → Secrets and variables → Actions):
   `GROQ_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`
6. Trigger a manual test run from the **Actions** tab → "Weekly AI & Tech
   Newsletter" → **Run workflow**, rather than waiting for Monday.
7. (Optional) Enable **GitHub Pages** on the `docs/` folder to get a
   browsable archive at `https://<you>.github.io/<repo>/`.

## Customizing

- **Sources / search queries:** edit `RSS_FEEDS`, `TAVILY_QUERIES` in
  `src/config.py`.
- **Filter strictness / output format:** edit `SYSTEM_PROMPT` in
  `src/summarize.py`.
- **LLM provider/model, rate-limit budget:** `LLM_MODEL`, `LLM_MAX_ITEMS`,
  `LLM_MAX_INPUT_CHARS` in `src/config.py` — tune these if you swap
  providers or hit a tokens-per-minute limit on a given model.
- **Schedule:** edit the `cron` line in `.github/workflows/newsletter.yml`.

## Known constraints

- Groq's free tier rate-limits by tokens-per-minute per model, which caps
  how many collected items can go into a single summarization call —
  `LLM_MAX_ITEMS` / `LLM_MAX_INPUT_CHARS` in `config.py` keep each run
  inside that budget. Swapping to a provider with a larger free-tier TPM
  budget, or splitting summarization into a map-reduce pass over batches,
  are both natural next steps if source volume grows.

## Possible extensions

- Map-reduce summarization (batch + combine) to remove the item-count cap
- Email delivery (e.g. free tier of Resend, or a Gmail SMTP step)
- A static site to browse past editions (GitHub Pages + simple template)
- De-duplication against previous weeks' coverage

---

### Resume bullet (example)

> Built and deployed an automated AI/tech news pipeline using LangGraph and
> LangChain, orchestrating parallel data collection across 5 sources (RSS,
> Hacker News, arXiv, GitHub, Tavily search), LLM-based deep-scraping via
> Firecrawl, and free-tier LLM summarization/ranking — scheduled via GitHub
> Actions for fully autonomous weekly publication at zero infrastructure
> cost.