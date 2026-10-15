from enum import auto
from core.config import settings
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base


Base=declarative_base()
engine=create_engine(settings.DataBaseUrl)
SessionLocal=sessionmaker(autoflush=False,
                    autocommit=False,
                    bind=engine)
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
