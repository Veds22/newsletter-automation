"""
Entry point. Run weekly (locally via `uv run main.py`, or via GitHub
Actions):

    uv run main.py

Builds the graph, runs it end to end, and writes:
  newsletters/YYYY-MM-DD.md   (this week's edition)
  docs/index.md               (running index, powers GitHub Pages if enabled)
"""
import os
import sys
import datetime as dt

from dotenv import load_dotenv
load_dotenv() 

import src.config as config    
from src.graph import build_graph  # noqa: E402


def main():
    today = dt.date.today()
    week_start = today - dt.timedelta(days=config.LOOKBACK_DAYS)
    date_range = f"{week_start.isoformat()} to {today.isoformat()}"

    print(f"Building newsletter for {date_range} ...")

    app = build_graph()
    initial_state = {
        "date_range": date_range,
        "raw_items": [],
        "enriched_content": {},
        "newsletter_markdown": "",
    }
    final_state = app.invoke(initial_state)

    newsletter_md = final_state["newsletter_markdown"]
    if not newsletter_md:
        raise SystemExit("Graph completed but produced no newsletter content - aborting.")

    os.makedirs(config.NEWSLETTER_DIR, exist_ok=True)
    os.makedirs(config.DOCS_DIR, exist_ok=True)

    out_path = os.path.join(config.NEWSLETTER_DIR, f"{today.isoformat()}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(newsletter_md)
    print(f"Wrote {out_path}")

    _update_index(today)


def _update_index(today: dt.date):
    """Maintain a simple running index of all past editions for GitHub Pages."""
    index_path = os.path.join(config.DOCS_DIR, "index.md")
    entries = sorted(os.listdir(config.NEWSLETTER_DIR), reverse=True)

    lines = ["# AI & Tech Weekly — Archive\n"]
    for fname in entries:
        if not fname.endswith(".md"):
            continue
        date_str = fname.replace(".md", "")
        lines.append(f"- [{date_str}](../{config.NEWSLETTER_DIR}/{fname})")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Updated {index_path}")


if __name__ == "__main__":
    main()