from fastapi import FastAPI
from app.db.db import engine, Base
from app.models import audio_files, projects, transcriptions, transcription_segments

Base.metadata.create_all(bind=engine)

app = FastAPI()
