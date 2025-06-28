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
from typing import List, Optional
import zipfile
import tempfile
from uuid import UUID
from app.core.config import upload_file_to_s3, delete_s3_folder, generate_presigned_url

router = APIRouter()

async def process_mp3_file(mp3_path, filename, project, project_name, base_folder, db):
    results = []
    base_filename = os.path.splitext(filename)[0]
    s3_base_path = f"{project_name}/{base_folder}"

    # Upload mp3 to S3
    with open(mp3_path, "rb") as f:
        mp3_data = f.read()
    mp3_key = f"{s3_base_path}/{filename}"
    upload_file_to_s3(mp3_data, mp3_key, filename)

    # Split and convert
    with tempfile.TemporaryDirectory() as tempdir:
        agent_path, customer_path = split_and_convert_audio(mp3_path, tempdir, base_filename)

        with open(agent_path, "rb") as f:
            agent_data = f.read()
        with open(customer_path, "rb") as f:
            customer_data = f.read()

        agent_key = f"{s3_base_path}/{os.path.basename(agent_path)}"
        customer_key = f"{s3_base_path}/{os.path.basename(customer_path)}"
        upload_file_to_s3(agent_data, agent_key, agent_path)
        upload_file_to_s3(customer_data, customer_key, customer_path)

        # Transcription
        agent_trans = await transcribe_audio_via_ws(agent_path)
        customer_trans = await transcribe_audio_via_ws(customer_path)
        duration = float(mediainfo(mp3_path)["duration"])

        audio_data = AudioFileCreate(
            project_id=project.id,
            filename=filename,
            file_path=mp3_key,
            duration_seconds=duration,
            channel_agent_path=agent_key,
            channel_customer_path=customer_key
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

@router.post("/upload-audio/", response_model=List[AudioFileResponse])
async def upload_audio(
    files: Optional[List[UploadFile]] = File(None),
    zip_file: Optional[UploadFile] = File(None),
    project_name: str = Form(...),
    db: Session = Depends(get_db)
):
    if zip_file and files:
        raise HTTPException(status_code=400, detail="Provide either 'zip_file' or 'files', not both.")
    elif not zip_file and not files:
        raise HTTPException(status_code=400, detail="No audio input provided.")

    results = []

    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")

    # ✅ ZIP FILE PATH
    if zip_file:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, zip_file.filename)

            with open(zip_path, "wb") as f:
                shutil.copyfileobj(zip_file.file, f)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            for root, _, file_list in os.walk(tmpdir):
                for name in file_list:
                    if name.lower().endswith(".mp3"):
                        full_path = os.path.join(root, name)
                        base_folder = os.path.basename(os.path.dirname(full_path))
                        results.extend(await process_mp3_file(full_path, name, project, project_name, base_folder, db))

    # ✅ INDIVIDUAL MP3 FILES
    elif files:
        for file in files:
            tmp_path = None
            try:
                # Save UploadFile to disk
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                    tmp_mp3.write(await file.read())
                    tmp_path = tmp_mp3.name
                results.extend(await process_mp3_file(tmp_path, file.filename, project, project_name, os.path.splitext(file.filename)[0], db))
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

    return results

@router.get("/", response_model=List[AudioFileResponse])
def read_audio_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    audio_files = crud_audio.get_audio_files(db, skip=skip, limit=limit)
    results = []

    for audio in audio_files:
        last_updated = db.query(func.max(Transcription.updated_at)) \
            .filter(Transcription.audio_id == audio.id) \
            .scalar()

        # สร้าง presigned URLs
        file_url = generate_presigned_url(audio.file_path)
        agent_url = generate_presigned_url(audio.channel_agent_path)
        customer_url = generate_presigned_url(audio.channel_customer_path)

        results.append(AudioFileResponse(
            id=audio.id,
            project_id=audio.project_id,
            filename=audio.filename,
            file_path=file_url,  # เปลี่ยนจาก path เป็น URL
            duration_seconds=audio.duration_seconds,
            channel_agent_path=agent_url,
            channel_customer_path=customer_url,
            created_at=audio.created_at,
            updated_at=last_updated or audio.updated_at,
            transcriptions=audio.transcriptions,
        ))

    return results

@router.get("/{audio_id}", response_model=AudioFileResponse)
def read_audio_file(audio_id: UUID, db: Session = Depends(get_db)):
    audio = crud_audio.get_audio_file(db, audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="AudioFile not found")

    last_updated = db.query(func.max(Transcription.updated_at)) \
        .filter(Transcription.audio_id == audio.id) \
        .scalar()

    file_url = generate_presigned_url(audio.file_path)
    agent_url = generate_presigned_url(audio.channel_agent_path)
    customer_url = generate_presigned_url(audio.channel_customer_path)

    return AudioFileResponse(
        id=audio.id,
        project_id=audio.project_id,
        filename=audio.filename,
        file_path=file_url,
        duration_seconds=audio.duration_seconds,
        channel_agent_path=agent_url,
        channel_customer_path=customer_url,
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