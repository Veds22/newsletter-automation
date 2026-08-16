"""
LangGraph node functions that wrap the two LLM-agent-native tools: 
"""

from langchain_tavily import TavilySearch
from firecrawl import FirecrawlApp
 
import src.config as config
from src.state import NewsletterState, RawItem


def search_tavily(sstate: NewsletterState) -> dict:
    """Node: run each configured query through Tavily and collect results."""
    search = TavilySearch(max_results=config.TAVILY_MAX_RESULTS_PER_QUERY)
    
    items: list[RawItem] = []
    for query in config.TAVILY_QUERIES:
        try:
            result = search.invoke({"query": query})
        except Exception as e:
            print(f"Error searching Tavily for query '{query}': {e}")
            continue
        
        results = result.get("results", []) if isinstance(result, dict) else []
        
        for r in results:
            items.append(RawItem(
                source="Tavily",
                type="search",
                title=r.get("title", ""),
                link=r.get("url", ""),
                summary=r.get("content", "")[:400],
                published=r.get("published_date"),
            ))
        
    print(f"[tavily] collected {len(items)} items across {len(config.TAVILY_QUERIES)} queries")
    return {"raw_items": items}
 
 

def enrich_with_firecrawl(state: NewsletterState) -> dict:
    """
    Node: fully scrape a small, capped number of the most promising items so
    the LLM gets full article text (not just a snippet) to summarize from.
 
    Only applied to "news"/"search" items - arXiv and GitHub items already
    carry enough structured content (abstract, description) on their own,
    so spending scarce Firecrawl credits there wouldn't add much.
    """
    app = FirecrawlApp()
    candidates = [
        it for it in state["raw_items"]
        if it["type"] in ("news", "search") and it["link"]
    ][:config.FIRECRAWL_MAX_PAGES_TO_ENRICH]
    
    enriched: dict[str, str] = {}
    for item in candidates:
        try:
            result = app.scrape_url(item["link"], formats=["markdown"])
            markdown = getattr(result, "markdown", None) or (
                result.get("markdown", "") if isinstance(result, dict) else ""
            )
            if markdown:
                enriched[item["link"]] = markdown[:6000]  # cap to keep prompt size sane
        except Exception as e:
            print(f"[firecrawl] failed to scrape {item['link']}: {e}")
            continue
        
    print(f"[firecrawl] enriched {len(enriched)} / {len(candidates)} candidate pages")
    return {"enriched_content": enriched}