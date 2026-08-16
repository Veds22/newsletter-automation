import datetime as dt
from email.utils import parsedate_to_datetime

import feedparser
import requests

import src.config as config
from src.state import NewsletterState, RawItem


def _cutoff() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=config.LOOKBACK_DAYS)


def collect_rss(State: NewsletterState) -> dict:
    """Node: pull recent entries from every configured RSS feed."""
    items: list[RawItem] = []
    cutoff = _cutoff()
    
    for source, url in config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"Error parsing RSS feed [rss] {source}: {e}")
            continue
        
        for entry in feed.entries:
            published = None
            for key in  ("published", "updated"):
                if key in entry:
                    try:
                        published = parsedate_to_datetime(entry[key])
                    except Exception as e:
                        published = None
                    break
            if published and published.tzinfo is None:
                published = published.replace(tzinfo=dt.timezone.utc)
            if published and published < cutoff:
                continue
            
            items.append(RawItem(
                source=source,
                type="news",
                title=entry.get("title", "").strip(),
                link=entry.get("link", ""),
                summary=(entry.get("summary", "") or "")[:400],
                published=published.isoformat() if published else None,
            ))
    print(f"[rss] collected {len(items)} items")
    return {"raw_items": items}


def collect_hn(state: NewsletterState) -> dict:
    """Node: pull recent Hacker News posts via Algolia API."""
    
    cutoff_ts = int(_cutoff().timestamp())
    params = {
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff_ts},points>{config.HN_MIN_POINTS}",
        "hitsPerPage": 100,
        "page": 0,
    }
    try:
        r = requests.get(config.HN_SEARCH_URL, params=params, timeout=20)
        r.raise_for_status()
        hits = r.json().get("hits", [])
    except Exception as e:
        print(f"Error fetching Hacker News posts: {e}")
        return {"raw_items": []}
    
    items: list[RawItem] = [
        RawItem(
         source="Hacker News",
            type="news",
            title=h.get("title") or "",
            link=h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            summary=f"{h.get('points', 0)} points, {h.get('num_comments', 0)} comments",
            published=h.get("created_at"),
        )
        for h in hits
    ]
    
    print(f"[hn] collected {len(items)} items")
    return {"raw_items": items}


def collect_arxiv(state: NewsletterState) -> dict:
    """Node: pull recent papers across configured categories from arXiv's free API."""
    import xml.etree.ElementTree as ET
    
    cat_query = "+OR+".join(f"cat:{cat}" for cat in config.ARXIV_CATEGORIES)
    params = {
        "search_query": cat_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": config.ARXIV_MAX_RESULTS,
    }
    
    try:
        r = requests.get(config.ARXIV_API_URL, params=params, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception as e:
        print(f"Error fetching arXiv papers: {e}")
        return {"raw_items": []}
    
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    cutoff = _cutoff()
    items: list[RawItem] = []
    
    for entry in root.findall("atom:entry", ns):
        published_raw = entry.findtext("atom:published", default="", namespaces=ns)
        try:
            published = dt.datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except Exception:
            published = None
        if published and published < cutoff:
            continue
    
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip().replace("\n", " ")[:400]
        link = entry.findtext("atom:id", default="", namespaces=ns) or ""
        items.append(RawItem(
            source="arXiv",
            type="research",
            title=title,
            link=link,
            summary=summary,
            published=published.isoformat() if published else None,
        ))

    print(f"[arxiv] collected {len(items)} items")
    return {"raw_items": items}



def collect_github(state: NewsletterState) -> dict:
    """Node: pull repos created recently and gaining stars fast, via GitHub's free Search API."""
    since = _cutoff().strftime("%Y-%m-%d")
    params = {
        "q": f"created:>{since} stars:>{config.GITHUB_MIN_STARS}",
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
    }
    headers = {"Accept": "application/vnd.github+json"}
    try:
        r = requests.get(config.GITHUB_SEARCH_URL, params=params, headers=headers, timeout=20)
        r.raise_for_status()
        repos = r.json().get("items", [])
    except Exception as e:
        print(f"[github] failed: {e}")
        return {"raw_items": []}
 
    items: list[RawItem] = [
        RawItem(
            source="GitHub",
            type="tool",
            title=repo.get("full_name", ""),
            link=repo.get("html_url", ""),
            summary=(repo.get("description") or "")[:300] + f" | stars: {repo.get('stargazers_count', 0)}",
            published=repo.get("created_at"),
        )
        for repo in repos
    ]
    print(f"[github] collected {len(items)} items")
    return {"raw_items": items}