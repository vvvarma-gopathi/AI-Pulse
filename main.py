from fastapi import Depends, FastAPI
from app.ingestion.fetch import SearchTechArticals
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.core.database import Base, engine, get_db
from app.start_productions.discovery import discover_recent_articles
from app.api.auth_route import auth_app
from app.api.articles_routes import articles_router
from app.api.chat_routes import chats_router
from app.api.projects_routes import projects_router
from app.api.research_routes import research_router
from app.services.auth_services import get_current_user
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app:FastAPI):
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=connection)
    yield

app=FastAPI(version="1.0.0",title="AIPulse",lifespan=lifespan)


origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/search')
async def summerize(user=Depends(get_current_user),db=Depends(get_db)):
    return await SearchTechArticals(user.user_name, db)

@app.get('/discover/existing/projects')
def discover_startups():
    return discover_recent_articles()



app.include_router(auth_app)
app.include_router(articles_router)
app.include_router(chats_router)
app.include_router(research_router)
app.include_router(projects_router)