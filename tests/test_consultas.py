import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app, obter_sessao


# BANCO DE DADOS EM MEMÓRIA PARA OS TESTES
engine_teste = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def obter_sessao_override():
    with Session(engine_teste) as session:
        yield session

app.dependency_overrides[obter_sessao] = obter_sessao_override

client = TestClient(app)

# ==========================================
# FIXTURE PARA CRIAR TODAS AS TABELAS NO BANCO
# ==========================================
@pytest.fixture(autouse=True)
def preparar_banco_de_dados():
    # Cria usuario e consulta no banco de testes
    SQLModel.metadata.create_all(engine_teste)
    yield
    # Limpa o banco após o teste terminar
    SQLModel.metadata.drop_all(engine_teste)

# ==========================================
# FUNÇÃO AUXILIAR PARA OBTER TOKEN NOS TESTES
# ==========================================
def obter_token_autenticado(email="paciente@exemplo.com", senha="senha_segura"):
    client.post("/cadastrar", json={"email": email, "senha": senha})
    resposta = client.post("/token", data={"username": email, "password": senha})
    return resposta.json()["access_token"]

# ==========================================
# TESTES DE CONSULTAS
# ==========================================
def test_criar_consulta_sucesso():
    token = obter_token_autenticado()
    
    resposta = client.post(
        "/consultas",
        json={
            "medico": "Dr. Silva",
            "data_hora": "2026-11-10T14:00:00",
            "observacoes": "Consulta de rotina"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    dados = resposta.json()
    assert resposta.status_code == 201
    assert dados["medico"] == "Dr. Silva"
    assert "id" in dados
    assert "usuario_id" in dados

def test_criar_consulta_sem_autenticacao():
    resposta = client.post(
        "/consultas",
        json={
            "medico": "Dr. Silva",
            "data_hora": "2026-11-10T14:00:00"
        }
    )
    assert resposta.status_code == 401

def test_listar_apenas_proprias_consultas():
    # Usuário 1 cria uma consulta
    token1 = obter_token_autenticado("user1@exemplo.com", "senha123")
    client.post(
        "/consultas",
        json={"medico": "Dr. Silva", "data_hora": "2026-11-10T14:00:00"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # Usuário 2 cria outra consulta
    token2 = obter_token_autenticado("user2@exemplo.com", "senha123")
    client.post(
        "/consultas",
        json={"medico": "Dra. Santos", "data_hora": "2026-11-12T10:00:00"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    # Usuário 1 busca suas consultas
    resposta = client.get(
        "/consultas",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    dados = resposta.json()
    assert resposta.status_code == 200
    assert len(dados) == 1
    assert dados[0]["medico"] == "Dr. Silva"

def test_cancelar_consulta_sucesso():
    token = obter_token_autenticado()
    
    # Criar consulta
    res_criacao = client.post(
        "/consultas",
        json={"medico": "Dr. Silva", "data_hora": "2026-11-10T14:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    consulta_id = res_criacao.json()["id"]
    
    # Cancelar (deletar) consulta
    res_delete = client.delete(
        f"/consultas/{consulta_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_delete.status_code == 204
    
    # Verificar que a lista agora está vazia
    res_lista = client.get("/consultas", headers={"Authorization": f"Bearer {token}"})
    assert len(res_lista.json()) == 0

def test_cancelar_consulta_de_outro_usuario():
    # Usuário 1 cria consulta
    token1 = obter_token_autenticado("user1@exemplo.com", "senha123")
    res_criacao = client.post(
        "/consultas",
        json={"medico": "Dr. Silva", "data_hora": "2026-11-10T14:00:00"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    consulta_id = res_criacao.json()["id"]
    
    # Usuário 2 tenta cancelar a consulta do Usuário 1
    token2 = obter_token_autenticado("user2@exemplo.com", "senha123")
    res_delete = client.delete(
        f"/consultas/{consulta_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert res_delete.status_code == 404