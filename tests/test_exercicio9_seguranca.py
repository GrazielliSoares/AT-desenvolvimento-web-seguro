import os
os.environ["TESTING"] = "1"

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database.connection import get_session
from security import gerar_hash_senha
from models.usuario import Usuario, PapelUsuario
from models.consulta import Consulta


# Banco SQLite em memória exclusivo para os testes
engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_override():
    with Session(engine_teste) as session:
        yield session


# Faz a aplicação usar o banco de teste
app.dependency_overrides[get_session] = get_session_override


@pytest.fixture(name="client")
def client_fixture():

    # Limpa completamente o banco antes de cada teste.
    # Isso evita o erro:
    # UNIQUE constraint failed: usuario.email
    SQLModel.metadata.drop_all(engine_teste)
    SQLModel.metadata.create_all(engine_teste)

    with Session(engine_teste) as session:

        # Paciente A
        paciente_a = Usuario(
            email="paciente_a@email.com",
            nome="Paciente A",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE
        )

        # Paciente B
        paciente_b = Usuario(
            email="paciente_b@email.com",
            nome="Paciente B",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE
        )

        # Profissional
        profissional = Usuario(
            email="medico@email.com",
            nome="Dr. Silva",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PROFISSIONAL
        )

        session.add(paciente_a)
        session.add(paciente_b)
        session.add(profissional)

        session.commit()

        session.refresh(paciente_a)
        session.refresh(paciente_b)
        session.refresh(profissional)

        # Consulta pertencente ao Paciente B
        #
        # IMPORTANTE:
        # data_hora precisa ser um objeto datetime,
        # e não uma string, porque o modelo Consulta
        # utiliza NaiveDatetime.
        consulta = Consulta(
            paciente_id=paciente_b.id,
            profissional_id=profissional.id,
            data_hora=datetime(2026, 10, 10, 10, 0, 0),
            status="agendada",
            observacoes="Consulta do Paciente B"
        )

        session.add(consulta)
        session.commit()

    with TestClient(app) as client:
        yield client

    # Limpa o banco depois do teste
    SQLModel.metadata.drop_all(engine_teste)


def test_bloqueio_bola_consulta_terceiros(client: TestClient):
    """
    Exercício 9:
    Paciente A tenta acessar uma consulta pertencente ao Paciente B.

    Resultado esperado:
    HTTP 403 Forbidden.
    """

    login_res = client.post(
        "/auth/login",
        data={
            "username": "paciente_a@email.com",
            "password": "senha123"
        }
    )

    assert login_res.status_code == 200

    token_a = login_res.json()["access_token"]

    response = client.get(
        "/consultas/1",
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    assert response.status_code == 403
    assert "Acesso negado" in response.json()["detail"]


def test_rejeicao_campos_extras(client: TestClient):
    """
    Exercício 9:
    Testa se a API rejeita campos que não foram declarados
    no modelo de entrada.

    Resultado esperado:
    HTTP 422 Unprocessable Entity.
    """

    login_res = client.post(
        "/auth/login",
        data={
            "username": "paciente_a@email.com",
            "password": "senha123"
        }
    )

    assert login_res.status_code == 200

    token_a = login_res.json()["access_token"]

    payload_extra = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-10T10:00:00",
        "status": "agendada",
        "observacoes": "Consulta normal",
        "campo_malicioso_extra": True
    }

    response = client.post(
        "/consultas/",
        json=payload_extra,
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    assert response.status_code == 422


def test_rejeicao_xss(client: TestClient):
    """
    Exercício 9:
    Testa a validação de entrada contra uma tentativa
    de XSS armazenado.

    O payload contém uma tag <script>, que não deve
    ser aceita pela validação da API.

    Resultado esperado:
    HTTP 422 Unprocessable Entity.
    """

    login_res = client.post(
        "/auth/login",
        data={
            "username": "paciente_a@email.com",
            "password": "senha123"
        }
    )

    assert login_res.status_code == 200

    token_a = login_res.json()["access_token"]

    payload_xss = {
        "paciente_id": 1,
        "profissional_id": 1,
        "data_hora": "2026-10-10T10:00:00",
        "status": "agendada",
        "observacoes": "<script>alert('XSS')</script>"
    }

    response = client.post(
        "/consultas/",
        json=payload_xss,
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    assert response.status_code == 422


def test_bloqueio_bola_prontuario(client: TestClient):
    """
    Exercício 9:
    Testa outro endpoint que possui o mesmo padrão
    de vulnerabilidade BOLA.

    Paciente A tenta acessar o prontuário do Paciente B.

    Resultado esperado:
    HTTP 403 Forbidden.
    """

    login_res = client.post(
        "/auth/login",
        data={
            "username": "paciente_a@email.com",
            "password": "senha123"
        }
    )

    assert login_res.status_code == 200

    token_a = login_res.json()["access_token"]

    response = client.get(
        "/pacientes/2/prontuario",
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    assert response.status_code == 403
    assert "Acesso negado" in response.json()["detail"]