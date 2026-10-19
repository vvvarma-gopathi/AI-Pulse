
from urllib.parse import urlsplit
from sqlalchemy.orm import Session
from app.ingestion.queries import QUERY
from app.ingestion.summerization import summarize_articles
from app.ingestion.web_search import normalize_url, search_articles
from app.websocket.manager import manager


# --------------------------------------------------
# PROCESS SEARCH RESULTS
# --------------------------------------------------

def process_articles(results, search_query: str = QUERY):
    unique_articles = {}

    for item in results:
        original_url = item.get("url", "").strip()

        if not original_url:
            continue

        normalized = normalize_url(original_url)

        if normalized in unique_articles:
            continue

        article_content = item.get("raw_content") or ""
        snippet = item.get("content") or ""

        unique_articles[normalized] = {
            "title": item.get("title", ""),
            "source_url": original_url,
            "normalized_url": normalized,
            "source_domain": urlsplit(original_url).netloc,
            "published_date": item.get("published_date"),
            "search_query": search_query,
            "relevance_score": item.get("score"),
            "snippet": snippet,
            "extracted_content": article_content,
            "content_status": (
                "extracted"
                if article_content.strip()
                else "snippet_only"
            ),
        }

    return list(unique_articles.values())


# --------------------------------------------------
# MAIN
# --------------------------------------------------

async def SearchTechArticals(
    user_name: str,
    db: Session,
    research_conditions: str | None = None,
):
    search_query = QUERY
    if research_conditions and research_conditions.strip():
        search_query = (
            f"{QUERY}\n\nAdditional research conditions:\n"
            f"{research_conditions.strip()}"
        )

    await manager.send_to_user(
        user_name=user_name,
        message={"data": "Searching the web for recent AI and IT news...."},
    )
    results, usage = search_articles(search_query)
    articles = process_articles(results, search_query)
    await manager.send_to_user(
        user_name=user_name,
        message={
            "data":f"credits using for this query is {usage['credits']}"
        }
    )
    if not articles:
        return []

    summaries = await summarize_articles(
        articles=articles,
        user_name=user_name,
        db=db,
    )
    for article in summaries['summaries']:
        await manager.send_to_user(
            user_name=user_name,
            message={
                "data":f"""Title:{article.title}
                  url:{article.url} 
                  Published_at:{article.published_at} Content:{article.summary} 
                  Technologies Involved{article.technologies}"""
            })
    return summaries['chat_id']