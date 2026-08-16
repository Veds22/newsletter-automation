"""
Wires every node (collectors.py, tools.py, and the LLM node in summarize.py)
into a single LangGraph StateGraph.
 
Shape of the graph:
 
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
 
The five collector/search nodes have no dependency on each other, so they
all fan out directly from START and LangGraph runs them concurrently.
enrich_with_firecrawl only fires once ALL five have finished (LangGraph
treats multiple incoming edges as a join), since it needs the complete
raw_items list to choose which pages to scrape.
"""


from langgraph.graph import StateGraph, START, END
 
from src.state import NewsletterState
from src.collectors import collect_rss, collect_hn, collect_arxiv, collect_github
from src.tools import search_tavily, enrich_with_firecrawl
from src.summarize import format_newsletter
 
COLLECTOR_NODES = (
    "collect_rss",
    "collect_hn",
    "collect_arxiv",
    "collect_github",
    "search_tavily",
)
 

def build_graph():
    graph = StateGraph(NewsletterState)
 
    graph.add_node("collect_rss", collect_rss)
    graph.add_node("collect_hn", collect_hn)
    graph.add_node("collect_arxiv", collect_arxiv)
    graph.add_node("collect_github", collect_github)
    graph.add_node("search_tavily", search_tavily)
    graph.add_node("enrich_with_firecrawl", enrich_with_firecrawl)
    graph.add_node("format_newsletter", format_newsletter)
 
    # Fan out: every source starts immediately, in parallel
    for node_name in COLLECTOR_NODES:
        graph.add_edge(START, node_name)

     # Fan in: enrich_with_firecrawl waits for ALL sources to finish
    for node_name in COLLECTOR_NODES:
        graph.add_edge(node_name, "enrich_with_firecrawl")
 
    graph.add_edge("enrich_with_firecrawl", "format_newsletter")
    graph.add_edge("format_newsletter", END)
 
    return graph.compile()


if __name__ == "__main__":
    # Sanity check: print the graph structure without actually running it
    app = build_graph()
    print(app.get_graph().draw_ascii())
