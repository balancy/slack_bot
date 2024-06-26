"""Module for defining the database schema."""

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Team(Base):
    """Team model."""

    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String, unique=True, index=True)
    team_name = Column(String)
    access_token = Column(String)


Base.metadata.create_all(bind=engine)
