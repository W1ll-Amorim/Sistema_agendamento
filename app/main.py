from fastapi import FastAPI
from database import engine
import models

app = FastAPI()

models.Base.metadata.create_all(dind=engine)

from database import SessionLocal
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()