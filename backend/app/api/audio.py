from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.core.audio_utils import split_and_convert_audio
from app.core.ws_transcribe import transcribe_audio_via_ws
from app.schemas.audio import AudioFileResponse, AudioFileCreate, JustAudioFileResponse
from app.crud import crud_audio, crud_transcription
from app.db.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Project, Transcription
import shutil, os
from uuid import uuid4
from pydub.utils import mediainfo
from app.schemas.transcription import TranscriptionCreate
from typing import List
import zipfile
import tempfile
from uuid import UUID

router = APIRouter()

UPLOAD_DIR = "/app/audio_uploads"
PROCESSED_DIR = "/app/processed_audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@router.post("/upload-audio/", response_model=List[AudioFileResponse])
async def upload_audio(
    files: List[UploadFile] = File(...),
    project_name: str = Form(...),
    db: Session = Depends(get_db)
):
    results = []

    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")

    for file in files:
        # ดึง base filename (ไม่มี .mp3)
        base_filename = os.path.splitext(file.filename)[0]

        upload_project_dir = os.path.join(UPLOAD_DIR, project_name)
        processed_project_dir = os.path.join(PROCESSED_DIR, project_name)
        os.makedirs(upload_project_dir, exist_ok=True)
        os.makedirs(processed_project_dir, exist_ok=True)

        upload_subdir = os.path.join(upload_project_dir, base_filename)
        processed_subdir = os.path.join(processed_project_dir, base_filename)
        os.makedirs(upload_subdir, exist_ok=True)
        os.makedirs(processed_subdir, exist_ok=True)

        # mp3_path → เก็บใน subfolder
        mp3_path = os.path.join(upload_subdir, f"{base_filename}.mp3")

        # Save original mp3
        with open(mp3_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # แยกเสียง → agent_path, customer_path จะถูกเก็บใน subfolder ด้วย
        agent_path, customer_path = split_and_convert_audio(
            mp3_path, processed_subdir, base_filename
        )

        # Transcribe
        agent_trans = await transcribe_audio_via_ws(agent_path)
        customer_trans = await transcribe_audio_via_ws(customer_path)

        # Duration
        duration = float(mediainfo(mp3_path)["duration"])

        # Save to DB
        audio_data = AudioFileCreate(
            project_id=project.id,
            filename=file.filename,
            file_path=mp3_path,
            duration_seconds=duration,
            channel_agent_path=agent_path,
            channel_customer_path=customer_path
        )
        db_audio = crud_audio.create_audio_file(db, audio_data)

        for channel, transcription_result in [("agent", agent_trans), ("customer", customer_trans)]:
            for seg in transcription_result.get("text_with_time", []):
                transcription_in = TranscriptionCreate(
                    audio_id=db_audio.id,
                    channel=channel,
                    start_time=seg["start"],
                    end_time=seg["end"],
                    original_text=seg["text"],
                    edited_text=seg["text"]
                )
                crud_transcription.create_transcription(db, transcription_in)

        results.append(db_audio)

    return results

@router.post("/upload-zip-audio/", response_model=List[AudioFileResponse])
async def upload_zip_audio(
    zip_file: UploadFile = File(...),
    project_name: str = Form(...),
    db: Session = Depends(get_db)
):
    results = []

    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")

    # ใช้ temp dir เพื่อเก็บไฟล์ zip ที่แตกออกมา
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, zip_file.filename)

        # Save zip file ลงดิสก์
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(zip_file.file, f)

        # แตก zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        # หา mp3 ทั้งหมดจาก zip ที่แตก
        for root, _, files in os.walk(tmpdir):
            for name in files:
                if name.lower().endswith(".mp3"):
                    full_path = os.path.join(root, name)
                    base_folder = os.path.basename(os.path.dirname(full_path))
                    base_filename = os.path.splitext(name)[0]

                    # เตรียมโฟลเดอร์ปลายทาง
                    upload_project_dir = os.path.join(UPLOAD_DIR, project_name)
                    processed_project_dir = os.path.join(PROCESSED_DIR, project_name)
                    os.makedirs(upload_project_dir, exist_ok=True)
                    os.makedirs(processed_project_dir, exist_ok=True)

                    upload_subdir = os.path.join(upload_project_dir, base_folder)
                    processed_subdir = os.path.join(processed_project_dir, base_folder)
                    os.makedirs(upload_subdir, exist_ok=True)
                    os.makedirs(processed_subdir, exist_ok=True)

                    # Copy mp3 จาก zip ไปยัง upload_subdir
                    target_mp3_path = os.path.join(upload_subdir, f"{base_filename}.mp3")
                    shutil.copy(full_path, target_mp3_path)

                    # แยกเสียง
                    agent_path, customer_path = split_and_convert_audio(
                        target_mp3_path, processed_subdir, base_filename
                    )

                    # Transcribe
                    agent_trans = await transcribe_audio_via_ws(agent_path)
                    customer_trans = await transcribe_audio_via_ws(customer_path)

                    duration = float(mediainfo(target_mp3_path)["duration"])

                    audio_data = AudioFileCreate(
                        project_id=project.id,
                        filename=name,
                        file_path=target_mp3_path,
                        duration_seconds=duration,
                        channel_agent_path=agent_path,
                        channel_customer_path=customer_path
                    )
                    db_audio = crud_audio.create_audio_file(db, audio_data)

                    for channel, transcription_result in [("agent", agent_trans), ("customer", customer_trans)]:
                        for seg in transcription_result.get("text_with_time", []):
                            transcription_in = TranscriptionCreate(
                                audio_id=db_audio.id,
                                channel=channel,
                                start_time=seg["start"],
                                end_time=seg["end"],
                                original_text=seg["text"],
                                edited_text=seg["text"]
                            )
                            crud_transcription.create_transcription(db, transcription_in)

                    results.append(db_audio)

    return results

@router.get("/", response_model=List[JustAudioFileResponse])
def read_audio_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    audio_files = crud_audio.get_audio_files(db, skip=skip, limit=limit)
    results = []

    for audio in audio_files:
        # หาวันเวลาล่าสุดจาก transcription
        last_updated = db.query(func.max(Transcription.updated_at)) \
            .filter(Transcription.audio_id == audio.id) \
            .scalar()

        results.append(JustAudioFileResponse(
            id=audio.id,
            project_id=audio.project_id,
            filename=audio.filename,
            file_path=audio.file_path,
            duration_seconds=audio.duration_seconds,
            channel_agent_path=audio.channel_agent_path,
            channel_customer_path=audio.channel_customer_path,
            created_at=audio.created_at,
            updated_at=last_updated or audio.updated_at,  # fallback ถ้าไม่มี transcription
            transcriptions=audio.transcriptions,
        ))

    return results

@router.get("/{audio_id}", response_model=JustAudioFileResponse)
def read_audio_file(audio_id: UUID, db: Session = Depends(get_db)):
    audio = crud_audio.get_audio_file(db, audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="AudioFile not found")

    # หาวันเวลาล่าสุดจาก transcription
    last_updated = db.query(func.max(Transcription.updated_at)) \
        .filter(Transcription.audio_id == audio.id) \
        .scalar()

    return JustAudioFileResponse(
        id=audio.id,
        project_id=audio.project_id,
        filename=audio.filename,
        file_path=audio.file_path,
        duration_seconds=audio.duration_seconds,
        channel_agent_path=audio.channel_agent_path,
        channel_customer_path=audio.channel_customer_path,
        created_at=audio.created_at,
        updated_at=last_updated or audio.updated_at,
        transcriptions=audio.transcriptions,
    )
