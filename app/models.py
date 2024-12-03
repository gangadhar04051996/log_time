from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)  # Ensure username is unique
    unique_id = Column(String(100), unique=True, nullable=False)  # Unique ID for the user

class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # Link logs to a user
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    interval = Column(String(50))
    description = Column(String(200))