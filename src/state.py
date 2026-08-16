"""
The shared state object that flows through every node in the LangGraph
pipeline. Each node reads from this and returns a partial update to it -
LangGraph merges updates in automatically based on the reducers below.
"""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class RawItem(TypedDict):
    """A single collected item, before filtering/ranking."""
    source: str        # e.g. "TechCrunch", "Hacker News", "arXiv", "GitHub", "Tavily"
    type: str          # "news" | "research" | "tool" | "search"
    title: str
    link: str
    summary: str        # short snippet/description
    published: str | None  # ISO date string, if known


class NewsletterState(TypedDict):
    # --- inputs ---
    date_range: str

    # --- accumulated across collector nodes ---
    raw_items: Annotated[list[RawItem], operator.add]

    # --- populated by the deep-scrape node (Firecrawl), keyed by link ---
    enriched_content: Annotated[dict[str, str], operator.or_]

    # --- populated by the LLM filter/rank/summarize node ---
    newsletter_markdown: str