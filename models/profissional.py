from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict

class ProfissionalBase(SQLModel):
    model_config = ConfigDict(extra="forbid")
    
    nome: str
    crm: str
    email: str
    especialidade: str

class Profissional(ProfissionalBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ProfissionalCreate(ProfissionalBase):
    pass

class ProfissionalRead(ProfissionalBase):
    id: int