from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from models.usuario import PapelUsuario
from routes.auth_routes import registrar_usuario
from security import verificar_ownership


def test_registro_rejeita_email_ja_cadastrado_com_mock():
    session = MagicMock(spec=Session)

    usuario_existente = MagicMock()
    session.exec.return_value.first.return_value = usuario_existente

    dados = {
        "email": "usuario@email.com",
        "senha": "senha123",
        "nome": "Usuário Teste",
        "papel": PapelUsuario.PACIENTE.value,
    }

    with pytest.raises(HTTPException) as excecao:
        registrar_usuario(dados, session)

    assert excecao.value.status_code == 400
    assert excecao.value.detail == "E-mail já cadastrado."

    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_ownership_rejeita_usuario_sem_permissao():
    usuario = MagicMock()
    usuario.id = 10
    usuario.papel = PapelUsuario.PACIENTE.value

    with pytest.raises(HTTPException) as excecao:
        verificar_ownership(
            usuario_atual=usuario,
            paciente_id=20,
            profissional_id=30
        )

    assert excecao.value.status_code == 403
    assert "Acesso negado" in excecao.value.detail


def test_ownership_permite_o_proprio_paciente():
    usuario = MagicMock()
    usuario.id = 10
    usuario.papel = PapelUsuario.PACIENTE.value

    resultado = verificar_ownership(
        usuario_atual=usuario,
        paciente_id=10,
        profissional_id=30
    )

    assert resultado is None


def test_ownership_permite_profissional_da_consulta():
    usuario = MagicMock()
    usuario.id = 30
    usuario.papel = PapelUsuario.PROFISSIONAL.value

    resultado = verificar_ownership(
        usuario_atual=usuario,
        paciente_id=10,
        profissional_id=30
    )

    assert resultado is None


def test_ownership_permite_administrador():
    usuario = MagicMock()
    usuario.id = 99
    usuario.papel = PapelUsuario.ADMIN.value

    resultado = verificar_ownership(
        usuario_atual=usuario,
        paciente_id=10,
        profissional_id=30
    )

    assert resultado is None
