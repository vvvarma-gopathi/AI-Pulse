def generate_discovery_queries(article) -> list[str]:
    technologies = article.technologies or []

    # Remove duplicates while preserving order.
    technologies = list(dict.fromkeys(
        tech.strip()
        for tech in technologies
        if isinstance(tech, str) and tech.strip()
    ))

    # Normalize and limit the summary.
    summary = " ".join((article.summary or "").split())[:250]

    tech_text = ", ".join(technologies[:5])

    # Generate exactly two focused discovery queries.
    if technologies:
        queries = [
            (
                f"""Existing startups, commercial products, open-source projects, and deployed applications using {tech_text} 
                for {summary}. Find real companies, launched products, repositories, and production case studies."""
            ),
        ]
    else:
        queries = [
           (
                f"""Existing startups, launched products, open-source projects, and deployed applications related to {summary}. 
                Prioritize real companies, working products, public repositories, and deployments."""
            ),
        ]

    return queries