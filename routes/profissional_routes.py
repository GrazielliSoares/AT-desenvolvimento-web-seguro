from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database.connection import get_session
from models.profissional import Profissional, ProfissionalCreate, ProfissionalRead

router = APIRouter(prefix="/profissionais", tags=["Profissionais de Saúde"])

@router.post("/", response_model=ProfissionalRead, status_code=status.HTTP_201_CREATED)
def criar_profissional(profissional: ProfissionalCreate, session: Session = Depends(get_session)):
    db_prof = Profissional.model_validate(profissional)
    session.add(db_prof)
    session.commit()
    session.refresh(db_prof)
    return db_prof

@router.get("/", response_model=List[ProfissionalRead])
def listar_profissionais(session: Session = Depends(get_session)):
    query = select(Profissional)
    return session.exec(query).all()