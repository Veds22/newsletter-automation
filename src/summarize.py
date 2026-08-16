"""
The final content node: takes everything collected (raw_items) plus any
deep-scraped full text (enriched_content), and asks the LLM to filter,
rank, and format it into the finished newsletter markdown - in one call.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

import src.config as config
from src.state import NewsletterState

SYSTEM_PROMPT = """You are an editor for a weekly AI/Tech newsletter. You will be given a \
large list of raw items (news articles, Hacker News posts, arXiv papers, \
trending GitHub repos, and web search results) collected over the past 7 \
days. Some items include a full scraped article body marked \
"[full article scraped]"; most only have a short snippet - treat both as \
valid, but prefer the fuller ones when you need real detail.

Your job: filter aggressively, then rank, then summarize. Apply "less news, \
more signal" - most raw items should be DISCARDED. Only keep items a busy, \
technically-informed person would genuinely want to know about. Merge \
duplicate stories covered by multiple sources into a single entry, citing \
the strongest source.

Topics in scope: AI, LLMs, agents, developer tools, cloud, cybersecurity, \
robotics, and major tech launches.

Output ONLY valid Markdown in exactly this structure, nothing before or after:

# 🗞️ AI & Tech Weekly — {date_range}

## 🔥 Top 5 Tech News
Numbered list. Each item: **Headline** — one to two sentence summary, then \
a line starting with "Why it matters:".

## 🧠 New AI/Tech Research
Bulleted list of the most interesting papers/findings. Each: **Title** — \
one sentence on the finding.

## 🛠️ New Tools & Products
Bulleted list of notable launches, frameworks, models, open-source projects. \
Each: **Name** — one sentence on what it does and why it's notable.

## 📈 Industry Updates
Bulleted list of company moves, funding, acquisitions. Each: one sentence.

## 🎯 What to Pay Attention To
3-5 bullets naming trends or developments worth watching, each with a short \
reason.

## 🔗 Sources
Markdown links for every item referenced above, grouped loosely by section.

Keep every summary tight. If a section genuinely has nothing signal-worthy \
this week, write "Nothing met the bar this week." under that heading \
instead of padding it."""

_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Here are this week's raw items:\n\n{items_text}"),
])


def _serialize_items(state: NewsletterState) -> str:
    """
    Turn raw_items (+ any enriched full text) into one compact text block,
    staying inside Groq's free-tier tokens-per-minute budget (see
    LLM_MAX_ITEMS / LLM_MAX_INPUT_CHARS in config.py).
    """
    enriched = state.get("enriched_content", {})

    # Hard cap on item COUNT first - a run that collects 400 raw items
    # shouldn't even attempt to serialize all of them before checking length.
    items = state["raw_items"][:config.LLM_MAX_ITEMS]

    lines = []
    total = 0

    for it in items:
        full_text = enriched.get(it["link"])
        # Enriched excerpts are capped shorter than before (600, not 1500) so
        # a handful of Firecrawl-scraped items can't dominate the budget.
        note = f"{full_text[:600]} ...[full article scraped]" if full_text else it["summary"]

        line = (
            f"- [{it['type']}] ({it['source']}) {it['title']} "
            f"| published: {it.get('published')} | link: {it['link']} "
            f"| note: {note}"
        )
        total += len(line)
        if total > config.LLM_MAX_INPUT_CHARS:
            break
        lines.append(line)

    print(f"[summarize] serialized {len(lines)}/{len(state['raw_items'])} "
          f"collected items (~{total // 4} tokens) for the LLM call")
    return "\n".join(lines)


def format_newsletter(state: NewsletterState) -> dict:
    """Node: filter, rank, and format everything collected into final markdown."""
    llm = ChatGroq(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)
    chain = _prompt | llm | StrOutputParser()

    items_text = _serialize_items(state)
    n_enriched = len(state.get("enriched_content", {}))
    print(f"[summarize] sending {len(state['raw_items'])} raw items "
          f"({n_enriched} with full scraped text) to {config.LLM_MODEL}")

    markdown = chain.invoke({
        "date_range": state["date_range"],
        "items_text": items_text,
    })

    return {"newsletter_markdown": markdown.strip()}