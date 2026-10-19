from app.rag.config import settings
from app.rag.schemas import ProjectRetrievalResult


def build_project_context(result: ProjectRetrievalResult) -> list[dict]:
    remaining = settings.max_context_characters
    context = []
    for project in result.projects:
        item = {
            "project_id": str(project.project_id),
            "name": project.name,
            "excerpt": project.excerpt,
            "relevance_score": round(project.relevance_score, 4),
            "technologies": project.technologies,
            "status": project.status,
            "goals": project.goals,
            "capabilities": project.capabilities,
            "limitations": project.limitations,
        }
        item_size = sum(len(str(value)) for value in item.values())
        if item_size > remaining:
            excerpt_limit = remaining - item_size + len(project.excerpt)
            if excerpt_limit <= 0:
                break
            item["excerpt"] = project.excerpt[:excerpt_limit]
            item_size = sum(len(str(value)) for value in item.values())
        context.append(item)
        remaining -= item_size
        if remaining <= 0:
            break
    return context
