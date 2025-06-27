from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.core.audio_utils import split_and_convert_audio
from app.core.ws_transcribe import transcribe_audio_via_ws
from app.schemas.audio import AudioFileResponse, AudioFileCreate
from app.crud import crud_audio, crud_transcription
from app.db.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Project, Transcription, AudioFile
import shutil, os
from uuid import uuid4
from pydub.utils import mediainfo
from app.schemas.transcription import TranscriptionCreate
from typing import List
import zipfile
import tempfile
from uuid import UUID
from app.core.config import upload_file_to_s3
from app.core.config import delete_s3_folder


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
        base_filename = os.path.splitext(file.filename)[0]
        
        upload_project_dir = os.path.join(UPLOAD_DIR, project_name)
        processed_project_dir = os.path.join(PROCESSED_DIR, project_name)
        os.makedirs(upload_project_dir, exist_ok=True)
        os.makedirs(processed_project_dir, exist_ok=True)

        upload_subdir = os.path.join(upload_project_dir, base_filename)
        processed_subdir = os.path.join(processed_project_dir, base_filename)
        os.makedirs(upload_subdir, exist_ok=True)
        os.makedirs(processed_subdir, exist_ok=True)

        mp3_path = os.path.join(upload_subdir, f"{base_filename}.mp3")

        with open(mp3_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        agent_path, customer_path = split_and_convert_audio(
            mp3_path, processed_subdir, base_filename
        )

        agent_trans = await transcribe_audio_via_ws(agent_path)

        customer_trans = await transcribe_audio_via_ws(customer_path)

        duration = float(mediainfo(mp3_path)["duration"])
        
        audio_data = AudioFileCreate(
            project_id=project.id,
            filename=file.filename,
            file_path=mp3_path,
            duration_seconds=duration,
            channel_agent_path=agent_path,
            channel_customer_path=customer_path
        )
        db_audio = crud_audio.create_audio_file(db, audio_data)

        s3_base_path = f"{project_name}/{base_filename}"

        uploaded_agent = upload_file_to_s3(agent_path, f"{s3_base_path}/{os.path.basename(agent_path)}")
        uploaded_customer = upload_file_to_s3(customer_path, f"{s3_base_path}/{os.path.basename(customer_path)}")
        uploaded_original = upload_file_to_s3(mp3_path, f"{s3_base_path}/{file.filename}")

        if not (uploaded_agent and uploaded_customer and uploaded_original):
            print(f"Warning: Some files failed to upload to S3 for {file.filename}")

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

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, zip_file.filename)

        with open(zip_path, "wb") as f:
            shutil.copyfileobj(zip_file.file, f)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        for root, _, files in os.walk(tmpdir):
            for name in files:
                if name.lower().endswith(".mp3"):
                    full_path = os.path.join(root, name)
                    base_folder = os.path.basename(os.path.dirname(full_path))
                    base_filename = os.path.splitext(name)[0]

                    upload_project_dir = os.path.join(UPLOAD_DIR, project_name)
                    processed_project_dir = os.path.join(PROCESSED_DIR, project_name)
                    os.makedirs(upload_project_dir, exist_ok=True)
                    os.makedirs(processed_project_dir, exist_ok=True)

                    upload_subdir = os.path.join(upload_project_dir, base_folder)
                    processed_subdir = os.path.join(processed_project_dir, base_folder)
                    os.makedirs(upload_subdir, exist_ok=True)
                    os.makedirs(processed_subdir, exist_ok=True)

                    target_mp3_path = os.path.join(upload_subdir, f"{base_filename}.mp3")
                    shutil.copy(full_path, target_mp3_path)

                    agent_path, customer_path = split_and_convert_audio(
                        target_mp3_path, processed_subdir, base_filename
                    )

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

                    # **อัปโหลดไฟล์ขึ้น S3**
                    s3_base_path = f"{project_name}/{base_folder}"
                    uploaded_agent = upload_file_to_s3(agent_path, f"{s3_base_path}/{os.path.basename(agent_path)}")
                    uploaded_customer = upload_file_to_s3(customer_path, f"{s3_base_path}/{os.path.basename(customer_path)}")
                    uploaded_original = upload_file_to_s3(target_mp3_path, f"{project_name}/{name}")

                    if not (uploaded_agent and uploaded_customer and uploaded_original):
                        print(f"Warning: Some files failed to upload to S3 for {name}")

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

@router.get("/", response_model=List[AudioFileResponse])
def read_audio_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    audio_files = crud_audio.get_audio_files(db, skip=skip, limit=limit)
    results = []

    for audio in audio_files:
        # หาวันเวลาล่าสุดจาก transcription
        last_updated = db.query(func.max(Transcription.updated_at)) \
            .filter(Transcription.audio_id == audio.id) \
            .scalar()

        results.append(AudioFileResponse(
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

@router.get("/{audio_id}", response_model=AudioFileResponse)
def read_audio_file(audio_id: UUID, db: Session = Depends(get_db)):
    audio = crud_audio.get_audio_file(db, audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="AudioFile not found")

    # หาวันเวลาล่าสุดจาก transcription
    last_updated = db.query(func.max(Transcription.updated_at)) \
        .filter(Transcription.audio_id == audio.id) \
        .scalar()

    return AudioFileResponse(
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

@router.delete("/audio/{audio_id}")
def delete_audio(audio_id: UUID, db: Session = Depends(get_db)):
    db_audio = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not db_audio:
        raise HTTPException(status_code=404, detail="Audio not found")

    # ดึงข้อมูลที่จำเป็น
    project_name = db_audio.project.name
    filename = os.path.splitext(db_audio.filename)[0]
    s3_folder_prefix = f"{project_name}/{filename}/"

    # 1️⃣ ลบจาก transcription ก่อน (foreign key)
    crud_transcription.delete_transcriptions_by_audio_id(db, audio_id)

    # 2️⃣ ลบข้อมูล AudioFile ออกจาก DB
    crud_audio.delete_audio_file(db, audio_id)

    # 3️⃣ ลบจาก S3
    delete_s3_folder(s3_folder_prefix)

    return {"detail": f"Audio ID {audio_id} and related files deleted successfully."}