from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from sqlmodel import Session, select

from database.connection import get_session
from config import settings

from models.usuario import Usuario, PapelUsuario


SECRET_KEY = settings.SECRET_KEY

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


password_hash = PasswordHash(
    (
        BcryptHasher(),
    )
)


def verificar_senha(
    senha_pura: str,
    senha_hash: str
) -> bool:
    return password_hash.verify(
        senha_pura,
        senha_hash
    )


def gerar_hash_senha(
    senha: str
) -> str:
    return password_hash.hash(
        senha
    )


def criar_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        +
        (
            expires_delta
            or timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update(
        {
            "exp": expire
        }
    )

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes={
        "read:horarios_disponiveis":
            "Permissão para consultar horários disponíveis (M2M / Laboratório)",

        "read:consultas":
            "Permissão para ler consultas",

        "write:consultas":
            "Permissão para criar e alterar consultas",

        "admin":
            "Acesso administrativo total"
    }
)


def verificar_token_e_escopos(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> dict:

    if security_scopes.scopes:
        authenticate_value = (
            f'Bearer scope="{security_scopes.scope_str}"'
        )
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={
            "WWW-Authenticate": authenticate_value
        }
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        token_scopes = payload.get(
            "scopes",
            []
        )

    except jwt.PyJWTError:
        raise credentials_exception

    for scope in security_scopes.scopes:

        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Escopo de acesso insuficiente. "
                    f"Escopo necessário: {scope}"
                ),
                headers={
                    "WWW-Authenticate": authenticate_value
                }
            )

    return payload


def obter_usuario_atual(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Usuario:

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    usuario = session.exec(
        select(Usuario).where(
            Usuario.email == email
        )
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )

    return usuario


def verificar_ownership(
    usuario_atual: Usuario,
    paciente_id: int,
    profissional_id: int
):
    e_dono = (
        usuario_atual.id == paciente_id
    )

    e_profissional = (
        usuario_atual.id == profissional_id
    )

    e_admin = (
        usuario_atual.papel == PapelUsuario.ADMIN
        or
        usuario_atual.papel == PapelUsuario.ADMIN.value
    )

    if not (
        e_dono
        or e_profissional
        or e_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Acesso negado: "
                "Você não possui permissão "
                "para acessar este recurso."
            )
        )


def exigir_papel(
    papel_requerido: PapelUsuario
):

    def verificador_papel(
        payload: dict = Depends(
            verificar_token_e_escopos
        )
    ):

        papel = payload.get("role")

        if (
            papel != papel_requerido.value
            and
            papel != PapelUsuario.ADMIN.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Acesso não autorizado "
                    "para o seu papel de usuário"
                )
            )

        return payload

    return verificador_papel