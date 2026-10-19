# One combined query covering all seven topics.
QUERY = (
    """Search the internet for relevant articles, technical blogs, research papers, and official announcements published within the last 7 days, based on the user's separately provided instructions.

Identify the user's goals, technologies, projects, and technical problems. Find recent AI tools, models, frameworks, libraries, open-source projects, and technology updates that directly support those goals. Prioritize practical implementation guides, new releases, technical improvements, benchmarks, and useful alternatives to existing technologies.

Prefer official documentation, engineering blogs, GitHub releases, research papers, and reputable technology publications. Return the most relevant results with the original URL, title, publisher, publication date, detailed available content, key findings, and practical relevance to the user's objectives.

Exclude duplicates, irrelevant news, outdated content, and unsupported claims. Verify dates and URLs, never fabricate content, and clearly identify partial article extraction. If relevant results are limited, return fewer results rather than unrelated content."""
)