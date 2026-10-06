from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class ConsultaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paciente_id: int
    profissional_id: int
    data_hora: str
    status: str = "agendada"
    observacoes: str | None = Field(default=None, max_length=500)

    @field_validator("observacoes")
    @classmethod
    def validar_observacoes(cls, value):
        if value is not None:
            # Whitelist:
            # permite letras, números, espaços e pontuação simples
            if not re.fullmatch(r"[a-zA-ZÀ-ÿ0-9\s.,!?-]*", value):
                raise ValueError("Observações contêm caracteres inválidos.")

        return value


class PacienteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=2, max_length=100)
    telefone: str

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, value):
        if not re.fullmatch(r"\+?[0-9]{10,15}", value):
            raise ValueError("Formato de telefone inválido.")

        return value