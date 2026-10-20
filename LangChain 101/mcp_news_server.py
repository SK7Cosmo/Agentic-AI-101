# Importing Packages
import feedparser
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("SK7SportsNewsServer")


def parse_rss_feed(feed_url: str, limit: int = 5) -> str:
    """Helper function to fetch and format RSS news items."""
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            return "No news items found."

        news_items = []
        for entry in feed.entries[:limit]:
            title = entry.get("title", "No Title")
            published = entry.get("published", entry.get("updated", "Unknown Date"))
            link = entry.get("link", "#")
            summary = entry.get("summary", "No details available.").strip()

            news_items.append(
                f"**{title}**\n"
                f"Published: {published}\n"
                f"Summary: {summary}\n"
                f"Link: {link}\n"
            )

        return "\n---\n".join(news_items)
    except Exception as e:
        return f"Error fetching news: {str(e)}"


@mcp.tool()
def get_cricket_news(limit: int = 5) -> str:
    """Fetches the latest cricket news, match updates, and headlines.

    Args:
        limit: Number of top news headlines to retrieve (default is 5).
    """
    # ESPN cricinfo RSS feed URL
    rss_url = "https://www.cricinfo.com/rss/content/story/feeds/0.xml"
    return parse_rss_feed(rss_url, limit)


@mcp.tool()
def get_tennis_news(limit: int = 5) -> str:
    """Fetches the latest tennis news, tournament updates, and player stats.

    Args:
        limit: Number of top news headlines to retrieve (default is 5).
    """
    # BBC Tennis RSS feed URL
    rss_url = "https://feeds.bbci.co.uk/sport/tennis/rss.xml"
    return parse_rss_feed(rss_url, limit)


@mcp.tool()
def get_football_news(limit: int = 5) -> str:
    """Fetches the latest football (soccer) news, transfer updates, and scores.

    Args:
        limit: Number of top news headlines to retrieve (default is 5).
    """
    # BBC Football RSS feed URL
    rss_url = "https://feeds.bbci.co.uk/sport/football/rss.xml"
    return parse_rss_feed(rss_url, limit)


if __name__ == "__main__":
    mcp.run(transport="stdio") # Local server