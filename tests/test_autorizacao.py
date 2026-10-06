import os
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app, obter_sessao, Usuario, gerar_hash_senha

# Engine do SQLite em memória exclusivo para testes
engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def obter_sessao_override():
    with Session(engine_teste) as session:
        yield session

# Sobrescreve a dependência de banco de dados do FastAPI
app.dependency_overrides[obter_sessao] = obter_sessao_override

@pytest.fixture(name="client")
def client_fixture():
    SQLModel.metadata.create_all(engine_teste)
    with TestClient(app) as client:
        yield client
    SQLModel.metadata.drop_all(engine_teste)

# FUNÇÃO DE TESTE (O nome PRECISA começar com test_)
def test_cadastrar_e_login(client: TestClient):
    # 1. Teste de cadastro
    resposta_cadastro = client.post("/cadastrar", json={
        "email": "teste@exemplo.com",
        "senha": "senha_segura"
    })
    assert resposta_cadastro.status_code == 201

    # 2. Teste de login
    resposta_login = client.post("/token", data={
        "username": "teste@exemplo.com",
        "password": "senha_segura"
    })
    assert resposta_login.status_code == 200
    assert "access_token" in resposta_login.json()