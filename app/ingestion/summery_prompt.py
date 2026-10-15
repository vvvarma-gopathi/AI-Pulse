SYSTEM_PROMPT = """
You are an AI technology intelligence summarizer.

Your task is to analyze a collection of technology articles
and produce a concise, information-dense summary for each article.

For every article:

1. Preserve the original article title.
2. Summarize the important information in 6-8 sentences.
3. Explain:
   - What was introduced, announced, or developed.
   - What problem it solves.
   - How the technology works at a high level.
   - Important use cases or applications.
4. Extract the technologies explicitly mentioned or clearly
   used in the article.
5. Include technologies, frameworks, libraries, models,
   platforms, protocols, databases, architectures, and
   important technical concepts.
6. Do not invent technologies that are not supported by
   the article.
7. Avoid generic terms such as "technology" or "software".
8. Do not include opinions or assumptions in the summary.
9. Keep the summary concise but retain technically important
   information.
10. Process every article provided in the input.

Return ONLY valid JSON matching this structure:

{
    "articles": [
        {
            "title": "string",
            "summary": "string",
            "url":"string",
            "published_at":"string"
            "technologies": [
                "string"
            ]
        }
    ]
}
"""

def build_article_prompt(articles: list[dict]) -> str:

    parts = [
        "Analyze the following technology articles.",
        "Process every article and return a summary for each one.",
        ""
    ]

    for index, article in enumerate(articles, start=1):

        parts.append(
            f"""
===== ARTICLE {index} =====

TITLE:
{article["title"]}

CONTENT:
{article["extracted_content"]}

PUBLISHED_AT:
{article['published_date']}

SNIPPET:
{article["snippet"]}


URL:
{article["source_url"]}

===== END ARTICLE {index} =====
"""
        )

    return "\n".join(parts)