from fastapi import Depends, FastAPI
from ingestion.fetch import SearchTechArticals
import asyncio
from core.database import Base,engine,get_db
from contextlib import asynccontextmanager
from start_productions.discovery import discover_recent_articles
from api.auth_route import auth_app
from api.research_routes import research_router
from services.auth_services import get_current_user

@asynccontextmanager
async def lifespan(app:FastAPI):
    db=get_db()
    Base.metadata.create_all(bind=engine)
    yield
    db.close()

app=FastAPI(version="1.0.0",title="AIPulse",lifespan=lifespan)

@app.get('/search')
async def summerize(user=Depends(get_current_user),db=Depends(get_db)):
    return await SearchTechArticals(user.user_name, db)

@app.get('/discover/existing/projects')
def discover_startups():
    return discover_recent_articles()

app.include_router(auth_app)
app.include_router(research_router)