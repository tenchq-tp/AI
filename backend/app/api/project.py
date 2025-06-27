from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.audio import AudioFileResponseForProject
from app.crud import crud_project
from app.db.db import get_db
from app.models.models import Transcription
from app.core.config import delete_s3_folder

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
def create_project(
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    project_data = ProjectCreate(name=name, description=description)
    return crud_project.create_project(db, project_data)

@router.get("/", response_model=List[ProjectResponse])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = crud_project.get_projects_all(db, skip=skip, limit=limit)
    results = []

    for project in projects:
        audio_file_count = len(project.audio_files)
        created_at = project.created_at

        audio_ids = [a.id for a in project.audio_files]
        last_updated = None
        if audio_ids:
            last_updated = db.query(func.max(Transcription.updated_at)) \
                .filter(Transcription.audio_id.in_(audio_ids)) \
                .scalar()

        # สร้าง list ของ AudioFileResponseForProject จาก project.audio_files
        audio_files_response = [
            AudioFileResponseForProject.from_orm(audio) for audio in project.audio_files
        ]

        results.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            audio_file_count=audio_file_count,
            created_at=created_at,
            last_transcription_updated_at=last_updated,
            audio_files=audio_files_response
        ))

    return results

@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(project_id: UUID, db: Session = Depends(get_db)):
    project = crud_project.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    audio_file_count = len(project.audio_files)
    created_at = project.created_at

    audio_ids = [a.id for a in project.audio_files]
    last_updated = None
    if audio_ids:
        last_updated = db.query(func.max(Transcription.updated_at)) \
            .filter(Transcription.audio_id.in_(audio_ids)) \
            .scalar()

    audio_files_response = [
        AudioFileResponseForProject.from_orm(audio) for audio in project.audio_files
    ]

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        audio_file_count=audio_file_count,
        created_at=created_at,
        last_transcription_updated_at=last_updated,
        audio_files=audio_files_response
    )
    
@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, project: ProjectUpdate, db: Session = Depends(get_db)):
    db_project = crud_project.update_project(db, project_id, project)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@router.delete("/{project_id}", response_model=ProjectResponse)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    db_project = crud_project.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ลบโฟลเดอร์บน S3 ก่อน
    s3_prefix = f"{db_project.name}/"
    delete_s3_folder(s3_prefix)
    
    db_project = crud_project.delete_project(db, project_id)

    return db_project