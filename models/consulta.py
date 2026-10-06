from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import ConfigDict, NaiveDatetime
from datetime import datetime, timezone

class ConsultaBase(SQLModel):
    model_config = ConfigDict(extra="forbid")
    
    paciente_id: int = Field(foreign_key="paciente.id")
    profissional_id: int = Field(foreign_key="profissional.id")
    data_hora: NaiveDatetime
    status: str = "agendada"
    observacoes: Optional[str] = None

class Consulta(ConsultaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Campos internos de auditoria (NÃO devem vazar na resposta JSON pública)
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notas_internas_auditoria: Optional[str] = Field(default="Auditoria interna - Acesso restrito")

class ConsultaCreate(ConsultaBase):
    pass

class ConsultaRead(SQLModel):
    """
    Response Model exposto pela API.
    Controla exatamente quais campos são devolvidos ao cliente, omitindo auditoria interna.
    """
    id: int
    paciente_id: int
    profissional_id: int
    data_hora: NaiveDatetime
    status: str
    observacoes: Optional[str] = None