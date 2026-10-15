from pydantic import BaseModel
from pydantic import Field
from datetime import datetime

class ArticleSummary(BaseModel):
    title:str
    summary:str
    url:str
    published_at:datetime
    technologies:list[str]

class ArticleSummaryResponse(BaseModel):
    articles: list[ArticleSummary]