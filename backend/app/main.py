from fastapi import FastAPI
from app.db.db import engine, Base
from app.models import models

Base.metadata.create_all(bind=engine)

app = FastAPI()
