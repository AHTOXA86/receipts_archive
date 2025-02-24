from sqlmodel import SQLModel, create_engine, Session
from ..core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, echo=True)

def init_db():
    # Create all tables in the database
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session 