from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict

class PacienteBase(SQLModel):
    model_config = ConfigDict(extra="forbid")
    
    nome: str
    cpf: str
    email: str
    telefone: str

class Paciente(PacienteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class PacienteCreate(PacienteBase):
    pass

class PacienteRead(PacienteBase):
    id: int