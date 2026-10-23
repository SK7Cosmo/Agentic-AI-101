# Importing Packages
import json
import urllib.parse
import urllib.request
from agents import function_tool


@function_tool
def search_books(query: str, limit: int = 3) -> str:
    """
    Searches the Open Library public API for books matching a given title or author name.

    Args:
        query (str): Book title, author name, or topic to search for.
        limit (int): Maximum number of search results to return (default is 3).

    Returns:
        str: JSON string containing book titles, authors, first publication years, and library keys.
    """
    try:
        # Encode string parameters for URL safety
        encoded_query = urllib.parse.quote(query)
        url = f"https://openlibrary.org/search.json?q={encoded_query}&limit={limit}"

        # Pass a custom User-Agent to prevent API blocking
        req = urllib.request.Request(
            url, headers={"User-Agent": "BookSearchAssistant/1.0"}
        )

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        docs = data.get("docs", [])
        if not docs:
            return json.dumps({"status": "empty", "message": f"No books found matching '{query}'."})

        results = []
        for book in docs[:limit]:
            results.append({
                "title": book.get("title", "Unknown Title"),
                "author": ", ".join(book.get("author_name", ["Unknown Author"])),
                "first_publish_year": book.get("first_publish_year", "N/A"),
                "edition_count": book.get("edition_count", 0),
                "open_library_url": f"https://openlibrary.org{book.get('key', '')}"
            })

        return json.dumps({"status": "success", "count": len(results), "books": results})

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to fetch book data: {str(e)}"})


