import os

os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from main import app
from database.connection import get_session
from models.usuario import Usuario, PapelUsuario
from security import gerar_hash_senha
from config import settings


engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool,
)


def get_session_override():
    with Session(engine_teste) as session:
        yield session


app.dependency_overrides[get_session] = get_session_override


def preparar_banco_teste():
    SQLModel.metadata.drop_all(engine_teste)
    SQLModel.metadata.create_all(engine_teste)


def test_configuracao_do_banco_vem_do_settings():
    assert settings.DATABASE_URL
    assert settings.SECRET_KEY


def test_sessao_do_banco_e_injetada_por_dependencia():
    preparar_banco_teste()

    assert callable(get_session)

    with Session(engine_teste) as session:
        usuario = Usuario(
            email="teste@email.com",
            nome="Usuário Teste",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE
        )

        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        assert usuario.id is not None


def test_sql_injection_nao_altera_consulta():
    preparar_banco_teste()

    with Session(engine_teste) as session:
        usuario = Usuario(
            email="usuario@email.com",
            nome="Usuário Seguro",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE
        )

        session.add(usuario)
        session.commit()

        # Tentativa de SQL Injection.
        email_malicioso = "' OR '1'='1"

        resultado = session.exec(
            select(Usuario).where(
                Usuario.email == email_malicioso
            )
        ).first()

        # A entrada maliciosa é tratada como valor,
        # e não como parte da instrução SQL.
        assert resultado is None


def test_api_continua_funcionando_com_banco_injetado():
    preparar_banco_teste()

    with Session(engine_teste) as session:
        usuario = Usuario(
            email="paciente@email.com",
            nome="Paciente Teste",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE
        )

        session.add(usuario)
        session.commit()

    with TestClient(app) as client:
        response = client.get("/")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


app.dependency_overrides.clear()