from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import Base

DATABASE_URL = "postgresql://user:password@db:5432/logger_db"
engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    Base.metadata.create_all(bind=engine)
