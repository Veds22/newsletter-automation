"""
Central configuration: 
"""

# --- RSS feeds (no auth required) -------------------------------------------------
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Wired": "https://www.wired.com/feed/rss",
    "The Register": "https://www.theregister.com/headlines.atom",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
}

# --- Hacker News (Algolia API, free, no key) --------------------------------------
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_MIN_POINTS = 50  # filter out low-signal posts

# --- arXiv (free, no key) ----------------------------------------------------------
ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.RO", "cs.CR"]
ARXIV_MAX_RESULTS = 40

# --- GitHub trending (via public Search API, free, no key needed for low volume) --
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
GITHUB_MIN_STARS = 200  # only repos gaining real traction

# --- Tavily search (LangChain tool, free tier ~1000 searches/mo) -------------------
# API key expected in env var: TAVILY_API_KEY  (langchain-tavily reads this itself)
TAVILY_QUERIES = [
    "major AI model release this week",
    "new AI agent framework or developer tool launch",
    "cybersecurity breach or vulnerability disclosed this week",
    "robotics breakthrough announcement",
    "AI startup funding round announced",
]
TAVILY_MAX_RESULTS_PER_QUERY = 5

# --- Firecrawl deep-scrape (free tier ~500 credits/mo) ------------------------------
# API key expected in env var: FIRECRAWL_API_KEY  (firecrawl-py reads this itself)
# Only scrape items flagged by the LLM as worth reading in full - keeps credit usage low.
FIRECRAWL_MAX_PAGES_TO_ENRICH = 5

# --- LLM (Groq free tier, via langchain-groq) --------------------------------------
# API key expected in env var: GROQ_API_KEY
LLM_MODEL = "openai/gpt-oss-120b"
LLM_TEMPERATURE = 0.3
LLM_MAX_ITEMS = 120
LLM_MAX_INPUT_CHARS = 20000

# --- Output ---------------------------------------------------------------------
LOOKBACK_DAYS = 7
NEWSLETTER_DIR = "newsletters"
DOCS_DIR = "docs"