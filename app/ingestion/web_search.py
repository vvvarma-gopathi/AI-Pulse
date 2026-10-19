from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from app.start_productions.web_search import client
from app.ingestion.queries import QUERY

MAX_RESULTS = 5
# --------------------------------------------------
# URL NORMALIZATION
# --------------------------------------------------

def normalize_url(url):
    """Normalize URLs to help identify duplicate articles."""
    try:
        parts = urlsplit(url)

        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
        }

        filtered_query = urlencode([
            (key, value)
            for key, value in parse_qsl(parts.query)
            if key.lower() not in tracking_params
        ])

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            filtered_query,
            "",
        ))

    except Exception:
        return url


# --------------------------------------------------
# SEARCH THE WEB
# --------------------------------------------------

def search_articles(query: str = QUERY):
    response = client.search(
        query=query,
        topic="news",
        search_depth="basic",
        max_results=MAX_RESULTS,
        include_raw_content="text",
        include_answer=False,
        include_usage=True,
    )

    # Preserve the reported API usage for cost monitoring.
    usage = response.get("usage", {})
    return response.get("results", []), usage