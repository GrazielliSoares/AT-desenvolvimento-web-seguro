from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database.connection import get_session
from models.usuario import Usuario, PapelUsuario
from models.paciente import Paciente, PacienteRead
from security import oauth2_scheme, SECRET_KEY, ALGORITHM
import jwt

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def obter_usuario_atual(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> Usuario:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return usuario


@router.get("/{paciente_id}/prontuario")
def obter_prontuario(
    paciente_id: int,
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    # --- CORREÇÃO DE BOLA NO ENDPOINT ADICIONAL ---
    if usuario_atual.papel == PapelUsuario.PACIENTE.value and usuario_atual.id != paciente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: Você só pode acessar seu próprio prontuário."
        )

    paciente = session.get(Usuario, paciente_id)
    if not paciente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado.")

    return {"id": paciente.id, "nome": paciente.nome, "email": paciente.email, "prontuario": "Dados confidenciais de saúde"}