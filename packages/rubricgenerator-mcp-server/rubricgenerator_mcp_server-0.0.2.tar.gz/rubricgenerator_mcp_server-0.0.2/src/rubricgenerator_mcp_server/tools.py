from langchain_teddynote.tools.tavily import TavilySearch


def web_search_tool(max_results):
    """Use the TavilySearch tool to find and recommend 2–3 books or online resources that are appropriate for the student's grade level and performance results, and relevant to the given topic."""
    web_search_tool = TavilySearch(max_results=max_results)
    return web_search_tool
