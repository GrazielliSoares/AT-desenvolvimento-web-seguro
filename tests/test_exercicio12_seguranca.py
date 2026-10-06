import os

os.environ["TESTING"] = "1"

from datetime import datetime

import pytest

from fastapi.testclient import TestClient

from sqlmodel import (
    SQLModel,
    Session,
    create_engine
)

from sqlmodel.pool import StaticPool

from main import app

from database.connection import get_session

from models.usuario import (
    Usuario,
    PapelUsuario
)

from models.consulta import Consulta

from security import gerar_hash_senha


# ============================================================
# BANCO DE DADOS DE TESTE
# ============================================================

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


# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture(name="client")
def client_fixture():
    SQLModel.metadata.drop_all(engine_teste)
    SQLModel.metadata.create_all(engine_teste)

    with Session(engine_teste) as session:
        paciente_a = Usuario(
            email="paciente_a@email.com",
            nome="Paciente A",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE.value
        )

        paciente_b = Usuario(
            email="paciente_b@email.com",
            nome="Paciente B",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PACIENTE.value
        )

        profissional = Usuario(
            email="profissional@email.com",
            nome="Profissional",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.PROFISSIONAL.value
        )

        admin = Usuario(
            email="admin@email.com",
            nome="Administrador",
            senha_hash=gerar_hash_senha("senha123"),
            papel=PapelUsuario.ADMIN.value,
            mfa_habilitado=True
        )

        session.add(paciente_a)
        session.add(paciente_b)
        session.add(profissional)
        session.add(admin)

        session.commit()

        session.refresh(paciente_a)
        session.refresh(paciente_b)
        session.refresh(profissional)
        session.refresh(admin)

        consulta_b = Consulta(
            paciente_id=paciente_b.id,
            profissional_id=profissional.id,
            data_hora=datetime(2026, 10, 10, 10, 0, 0),
            status="agendada",
            observacoes="Consulta privada do Paciente B"
        )

        session.add(consulta_b)
        session.commit()

    with TestClient(app) as client:
        yield client

    SQLModel.metadata.drop_all(engine_teste)


# ============================================================
# FUNÇÃO AUXILIAR DE LOGIN
# ============================================================

def obter_token(
    client: TestClient,
    email: str,
    senha: str,
    mfa_code: str | None = None
):
    dados = {
        "username": email,
        "password": senha
    }

    if mfa_code is not None:
        dados["mfa_code"] = mfa_code

    resposta = client.post(
        "/auth/login",
        data=dados
    )

    assert resposta.status_code == 200

    return resposta.json()["access_token"]


# ============================================================
# 1 — ACESSO SEM AUTENTICAÇÃO
# ============================================================

def test_endpoint_protegido_exige_autenticacao(client: TestClient):
    resposta = client.get("/consultas/")

    assert resposta.status_code == 401


# ============================================================
# 2 — TOKEN INVÁLIDO
# ============================================================

def test_token_invalido_e_rejeitado(client: TestClient):
    resposta = client.get(
        "/consultas/",
        headers={
            "Authorization": "Bearer token_invalido"
        }
    )

    assert resposta.status_code == 401


# ============================================================
# 3 — BOLA EM CONSULTA
# ============================================================

def test_paciente_nao_acessa_consulta_de_outro_paciente(
    client: TestClient
):
    token_paciente_a = obter_token(
        client,
        "paciente_a@email.com",
        "senha123"
    )

    resposta = client.get(
        "/consultas/1",
        headers={
            "Authorization": f"Bearer {token_paciente_a}"
        }
    )

    assert resposta.status_code == 403
    assert "Acesso negado" in resposta.json()["detail"]


# ============================================================
# 4 — BOLA EM PRONTUÁRIO
# ============================================================

def test_paciente_nao_acessa_prontuario_de_outro(
    client: TestClient
):
    token_paciente_a = obter_token(
        client,
        "paciente_a@email.com",
        "senha123"
    )

    resposta = client.get(
        "/pacientes/2/prontuario",
        headers={
            "Authorization": f"Bearer {token_paciente_a}"
        }
    )

    assert resposta.status_code == 403
    assert "Acesso negado" in resposta.json()["detail"]


# ============================================================
# 5 — ABUSO DE ESCOPO M2M
# ============================================================

def test_cliente_m2m_nao_pode_solicitar_escopo_nao_autorizado(
    client: TestClient
):
    resposta = client.post(
        "/auth/m2m/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "lab_parceiro_id",
            "client_secret": "secret_super_seguro_laboratorio_123",
            "scope": "read:consultas"
        }
    )

    assert resposta.status_code == 403
    assert "não é permitido" in resposta.json()["detail"]


# ============================================================
# 6 — CREDENCIAL M2M INVÁLIDA
# ============================================================

def test_credencial_m2m_invalida_e_rejeitada(
    client: TestClient
):
    resposta = client.post(
        "/auth/m2m/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "lab_parceiro_id",
            "client_secret": "senha_errada",
            "scope": "read:horarios_disponiveis"
        }
    )

    assert resposta.status_code == 401


# ============================================================
# 7 — ACESSO ADMINISTRATIVO SEM PAPEL ADMIN
# ============================================================

def test_paciente_nao_acessa_area_administrativa(
    client: TestClient
):
    token_paciente = obter_token(
        client,
        "paciente_a@email.com",
        "senha123"
    )

    resposta = client.get(
        "/admin/relatorio-sistema",
        headers={
            "Authorization": f"Bearer {token_paciente}"
        }
    )

    assert resposta.status_code == 403


# ============================================================
# 8 — SQL INJECTION
# ============================================================

def test_sql_injection_nao_bypassa_autenticacao(
    client: TestClient
):
    resposta = client.post(
        "/auth/login",
        data={
            "username": "' OR '1'='1",
            "password": "' OR '1'='1"
        }
    )

    assert resposta.status_code in [400, 401]
    assert "access_token" not in resposta.json()


# ============================================================
# 9 — XSS
# ============================================================

def test_xss_e_rejeitado(client: TestClient):
    token = obter_token(
        client,
        "paciente_a@email.com",
        "senha123"
    )

    payload_xss = "<script>alert('XSS')</script>"

    resposta = client.post(
        "/consultas/",
        json={
            "paciente_id": 1,
            "profissional_id": 3,
            "data_hora": "2026-11-10T10:00:00",
            "status": "agendada",
            "observacoes": payload_xss
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 422


# ============================================================
# 10 — CAMPOS EXTRAS
# ============================================================

def test_campos_nao_declarados_sao_rejeitados(
    client: TestClient
):
    token = obter_token(
        client,
        "paciente_a@email.com",
        "senha123"
    )

    resposta = client.post(
        "/consultas/",
        json={
            "paciente_id": 1,
            "profissional_id": 3,
            "data_hora": "2026-11-10T10:00:00",
            "status": "agendada",
            "observacoes": "Consulta normal",
            "campo_malicioso": "tentativa"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert resposta.status_code == 422


# ============================================================
# 11 — HEADERS DE SEGURANÇA
# ============================================================

def test_headers_de_seguranca_estao_presentes(
    client: TestClient
):
    resposta = client.get("/")

    assert resposta.status_code == 200

    assert (
        resposta.headers.get("Strict-Transport-Security")
        is not None
    )

    assert (
        resposta.headers.get("X-Frame-Options")
        == "DENY"
    )

    assert (
        resposta.headers.get("X-Content-Type-Options")
        == "nosniff"
    )


# ============================================================
# 12 — CORS
# ============================================================

def test_cors_nao_permite_origem_desconhecida(
    client: TestClient
):
    resposta = client.get(
        "/",
        headers={
            "Origin": "https://site-malicioso.com"
        }
    )

    assert (
        resposta.headers.get("access-control-allow-origin")
        != "https://site-malicioso.com"
    )