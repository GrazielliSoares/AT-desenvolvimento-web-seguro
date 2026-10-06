from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Security
)

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session, select

from database.connection import get_session

from models.consulta import Consulta, ConsultaRead
from schemas import ConsultaCreate
from models.usuario import Usuario, PapelUsuario

from security import (
    verificar_token_e_escopos,
    obter_usuario_atual,
    verificar_ownership
)


router = APIRouter(
    prefix="/consultas",
    tags=["Consultas"]
)

templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "/horarios-disponiveis",
    summary="Consultar horários disponíveis"
)
def listar_horarios_disponiveis(
    token_payload: dict = Security(
        verificar_token_e_escopos,
        scopes=["read:horarios_disponiveis"]
    ),
    session: Session = Depends(get_session)
):
    """
    Endpoint destinado à integração M2M.

    O acesso depende do escopo:
    read:horarios_disponiveis
    """

    query = (
        select(
            Consulta.data_hora,
            Consulta.status
        )
        .where(Consulta.status == "agendada")
    )

    agendamentos = session.exec(query).all()

    return {
        "cliente_solicitante": token_payload.get(
            "client_name",
            token_payload.get("sub")
        ),
        "tipo_acesso": token_payload.get("type"),
        "agendamentos_ocupados": [
            {
                "data_hora": str(item[0]),
                "status": item[1]
            }
            for item in agendamentos
        ]
    }


@router.post(
    "/",
    response_model=ConsultaRead,
    status_code=status.HTTP_201_CREATED
)
def criar_consulta(
    consulta: ConsultaCreate,
    token_payload: dict = Security(
        verificar_token_e_escopos,
        scopes=["write:consultas"]
    ),
    session: Session = Depends(get_session)
):
    """
    Cria uma nova consulta.

    A validação do payload é realizada pelo modelo
    ConsultaCreate.
    """

    db_consulta = Consulta.model_validate(consulta)

    session.add(db_consulta)
    session.commit()
    session.refresh(db_consulta)

    return db_consulta


@router.get(
    "/",
    response_model=List[ConsultaRead]
)
def listar_consultas(
    token_payload: dict = Security(
        verificar_token_e_escopos,
        scopes=["read:consultas"]
    ),
    session: Session = Depends(get_session)
):
    """
    Lista consultas.

    O acesso exige o escopo read:consultas.
    """

    query = select(Consulta)

    return session.exec(query).all()


@router.get(
    "/{consulta_id}",
    response_model=ConsultaRead
)
def obter_consulta(
    consulta_id: int,
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(obter_usuario_atual)
):
    """
    Consulta uma consulta específica.

    Proteção contra BOLA:
    o usuário só pode acessar uma consulta se:

    - for o paciente da consulta;
    - for o profissional da consulta;
    - ou for administrador.
    """

    consulta = session.get(
        Consulta,
        consulta_id
    )

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consulta não encontrada."
        )

    verificar_ownership(
        usuario_atual=usuario_atual,
        paciente_id=consulta.paciente_id,
        profissional_id=consulta.profissional_id
    )

    return consulta


@router.get(
    "/agenda-html",
    response_class=HTMLResponse,
    tags=["Recepção HTML"]
)
def visualizar_agenda_html(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Página HTML interna da recepção.

    O template Jinja2 utiliza autoescape por padrão,
    evitando que valores armazenados sejam interpretados
    como HTML/JavaScript.
    """

    query = select(Consulta)

    consultas = session.exec(query).all()

    return templates.TemplateResponse(
        "agenda.html",
        {
            "request": request,
            "consultas": consultas
        }
    )