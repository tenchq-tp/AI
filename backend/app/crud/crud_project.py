from sqlalchemy.orm import Session
from uuid import UUID
from app.models.models import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

def get_project_by_id(db: Session, project_id: UUID):
    return db.query(Project).filter(Project.id == project_id).first()

def get_projects_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Project).offset(skip).limit(limit).all()

def create_project(db: Session, project: ProjectCreate):
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, project_id: UUID, project: ProjectUpdate):
    db_project = get_project_by_id(db, project_id)
    if db_project:
        for key, value in project.dict().items():
            setattr(db_project, key, value)
        db.commit()
        db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: UUID):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project:
        db.delete(db_project)
        db.commit()
        return db_project
    return None

