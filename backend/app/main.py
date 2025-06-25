from fastapi import FastAPI
from app.db.db import engine, Base
from app.models import models
from app.api import audio, project, transcription

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(project.router, prefix="/api/projects", tags=["projects"])
app.include_router(audio.router, prefix="/api/audio", tags=["audios"])
app.include_router(transcription.router, prefix="/api", tags=["transcriptions"])

