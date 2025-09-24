from sqlmodel import SQLModel, create_engine, Session
import os

DB_URL = os.getenv("RICO_DB_URL", "sqlite:///./rico_ops_v2.db")
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def session():
    return Session(engine)
