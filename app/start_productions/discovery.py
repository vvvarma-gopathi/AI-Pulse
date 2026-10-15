
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.articles_model import ArticleSummary
from models.articles_model import DiscoveredProduct
from websocket.manager import manager
from start_productions.web_search import search_web
from start_productions.query_generator import generate_discovery_queries

async def discover_for_article(
    db: Session,
    user_name:str,
    chat_id:str,
    article: ArticleSummary,
) -> dict:
    queries = generate_discovery_queries(article)

    # Prevent the same URL being processed repeatedly
    # for this article during one run.
    seen_urls = {article.url.rstrip("/").lower()}
    saved = 0
    skipped = 0

    try:
        for query in queries:
            results = search_web(query, max_results=2)

            for item in results:
                candidate_url = item["url"].strip()
                normalized_url = candidate_url.rstrip("/").lower()

                if normalized_url in seen_urls:
                    continue

                seen_urls.add(normalized_url)

                # Check the database too, in case this candidate
                # was stored during an earlier run.
                existing = db.execute(
                    select(DiscoveredProduct.id).where(
                        DiscoveredProduct.article_summary_id
                        == article.id,
                        DiscoveredProduct.candidate_url
                        == candidate_url,
                        DiscoveredProduct.chat_id==chat_id
                    )
                ).scalar_one_or_none()

                if existing:
                    skipped += 1
                    continue

                candidate = DiscoveredProduct(
                    article_summary_id=article.id,
                    name=item["title"][:500],
                    candidate_url=candidate_url,
                    description=item["content"],
                    search_query=query,
                    evidence_status="unverified",
                    chat_id=chat_id
                )
                await manager.send_to_user(user_name,message={"data":{
                    'Title': item["title"][:500],
                    'Description': item["content"],
                    'CandidateURL': candidate_url,
                }})

                db.add(candidate)
                saved += 1

        db.commit()

        return {
            "article_title": article.title,
            "queries_run": len(queries),
            "candidates_saved": saved,
            "duplicates_skipped": skipped,
        }

    except Exception:
        db.rollback()
        raise


async def discover_recent_articles(chat_id,user_name) -> list[dict]:
    db = SessionLocal()

    try:
        articles = db.execute(
            select(ArticleSummary).where(ArticleSummary.chat_id==chat_id)
        ).scalars().all()

        await manager.send_to_user(user_name,message={"data":{
            'message': f"Found {len(articles)} articles for chat_id {chat_id} started discovering the startups for each article. This may take a while, please be patient."
        }})

        reports = []

        for article in articles:
            report = await discover_for_article(db, user_name, chat_id, article)
            reports.append(report)
        return reports

    finally:
        db.close()
