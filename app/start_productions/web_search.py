
from dotenv import load_dotenv
from tavily import TavilyClient
from app.core.config import settings
from fastapi import HTTPException,status

if settings.TalivyApi:
    client = TavilyClient(api_key=settings.TalivyApi)
else:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="NO talivy api key found in env.")


def search_web(
    query: str,
    max_results: int = 5,
) -> list[dict]:
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
    )

    results = []

    for item in response.get("results", []):
        url = item.get("url")
        title = item.get("title")
        content = item.get("content")

        if not url or not title:
            continue

        results.append({
            "title": title,
            "url": url,
            "content": content or "",
            "score": item.get("score"),
        })

    return results
