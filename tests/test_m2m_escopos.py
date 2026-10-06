import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database.connection import get_session

engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def get_session_override():
    with Session(engine_teste) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

@pytest.fixture(name="client")
def client_fixture():
    SQLModel.metadata.create_all(engine_teste)
    with TestClient(app) as client:
        yield client
    SQLModel.metadata.drop_all(engine_teste)

def test_m2m_laboratorio_fluxo_escopos(client: TestClient):
    # 1. Autenticação M2M do laboratório via Client Credentials
    resposta_token = client.post("/auth/m2m/token", data={
        "grant_type": "client_credentials",
        "client_id": "lab_parceiro_id",
        "client_secret": "secret_super_seguro_laboratorio_123",
        "scope": "read:horarios_disponiveis"
    })
    assert resposta_token.status_code == 200
    token_lab = resposta_token.json()["access_token"]

    # 2. Acesso permitido ao endpoint com escopo correto
    res_horarios = client.get(
        "/consultas/horarios-disponiveis",
        headers={"Authorization": f"Bearer {token_lab}"}
    )
    assert res_horarios.status_code == 200
    assert res_horarios.json()["tipo_acesso"] == "m2m_token"

    # 3. Bloqueio ao tentar acessar rotas sem o escopo necessário (ex: leitura de consultas de pacientes)
    res_bloqueado = client.get(
        "/consultas/",
        headers={"Authorization": f"Bearer {token_lab}"}
    )
    assert res_bloqueado.status_code == 403