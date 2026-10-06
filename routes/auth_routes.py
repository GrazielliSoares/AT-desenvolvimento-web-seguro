from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from database.connection import get_session
from models.usuario import Usuario, PapelUsuario
from security import verificar_senha, criar_access_token, gerar_hash_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Cadastro M2M de parceiros autorizados
CLIENTES_M2M_AUTORIZADOS = {
    "lab_parceiro_id": {
        "client_secret": "secret_super_seguro_laboratorio_123",
        "client_name": "Laboratório de Exames Parceiro",
        "allowed_scopes": ["read:horarios_disponiveis"]
    }
}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar_usuario(dados: dict, session: Session = Depends(get_session)):
    email = dados.get("email")
    senha = dados.get("senha")
    papel = dados.get("papel", PapelUsuario.PROFISSIONAL.value)

    statement = select(Usuario).where(Usuario.email == email)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    novo_usuario = Usuario(
        email=email,
        nome=dados.get("nome", "Usuário"),
        senha_hash=gerar_hash_senha(senha),
        papel=papel,
        mfa_habilitado=(papel == PapelUsuario.ADMIN.value)
    )
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return {"message": "Usuário cadastrado com sucesso", "id": novo_usuario.id}

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    mfa_code: str = None,
    session: Session = Depends(get_session)
):
    statement = select(Usuario).where(Usuario.email == form_data.username)
    usuario = session.exec(statement).first()

    if not usuario or not verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos.")

    if usuario.papel == PapelUsuario.ADMIN and usuario.mfa_habilitado:
        if mfa_code != "123456":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA obrigatório para administradores. Informe mfa_code=123456."
            )

    scopes = ["read:consultas", "write:consultas"]
    if usuario.papel == PapelUsuario.ADMIN:
        scopes.append("admin")

    token_data = {
        "sub": usuario.email,
        "role": usuario.papel,
        "type": "user_session",
        "scopes": scopes
    }
    access_token = criar_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer", "scopes": scopes}

@router.post("/m2m/token", summary="Autenticação M2M - Client Credentials Grant")
def login_m2m_client_credentials(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(default="read:horarios_disponiveis")
):
    """
    Fluxo OAuth 2.0 Client Credentials Grant para integração de parceiros externos (Laboratório).
    """
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="grant_type inválido. Utilize 'client_credentials'."
        )

    cliente = CLIENTES_M2M_AUTORIZADOS.get(client_id)
    if not cliente or cliente["client_secret"] != client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="client_id ou client_secret inválidos."
        )

    requested_scopes = scope.split(" ") if scope else []
    for s in requested_scopes:
        if s not in cliente["allowed_scopes"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"O escopo '{s}' não é permitido para este cliente M2M."
            )

    token_data = {
        "sub": client_id,
        "client_name": cliente["client_name"],
        "type": "m2m_token",
        "scopes": requested_scopes
    }
    access_token = criar_access_token(data=token_data)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "scope": " ".join(requested_scopes)
    }