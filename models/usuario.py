from typing import Optional
from enum import Enum
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict, EmailStr

class PapelUsuario(str, Enum):
    PACIENTE = "paciente"
    PROFISSIONAL = "profissional"
    ADMIN = "admin"

class UsuarioBase(SQLModel):
    model_config = ConfigDict(extra="forbid")
    
    email: EmailStr = Field(unique=True, index=True)
    nome: str
    papel: PapelUsuario = Field(default=PapelUsuario.PACIENTE)
    mfa_habilitado: bool = Field(default=False)

class Usuario(UsuarioBase, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    senha_hash: str
    mfa_secret: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioRead(UsuarioBase):
    id: int

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(SQLModel):
    email: Optional[str] = None
    papel: Optional[str] = None
    mfa_verificado: bool = False