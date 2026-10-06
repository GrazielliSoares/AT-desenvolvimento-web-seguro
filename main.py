import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from database.connection import create_db_and_tables

from routes.auth_routes import router as auth_router
from routes.consulta_routes import router as consulta_router
from routes.paciente_routes import router as paciente_router
from routes.profissional_routes import router as profissional_router
from routes.admin_routes import router as admin_router

from iast import registrar_evento_iast


app = FastAPI(
    title="API de Agendamento de Consultas",
    description=(
        "Sistema seguro com suporte a RBAC, MFA e "
        "integração M2M via escopos OAuth2."
    ),
    version="1.0.0"
)


# ==========================================================
# CORS
# ==========================================================

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ==========================================================
# IAST — INSTRUMENTAÇÃO DE RUNTIME
# ==========================================================

@app.middleware("http")
async def iast_runtime_monitor(request: Request, call_next):
    response = await call_next(request)

    registrar_evento_iast(
        metodo=request.method,
        caminho=request.url.path,
        status_code=response.status_code,
        observacao="requisicao observada durante a execucao da aplicacao"
    )

    return response


# ==========================================================
# HEADERS DE SEGURANÇA
# ==========================================================

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    # HSTS:
    # instrui o navegador a utilizar HTTPS nas próximas conexões
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    # Impede que a aplicação seja carregada dentro de
    # iframe/frame de outro site.
    response.headers["X-Frame-Options"] = "DENY"

    # Impede que o navegador tente interpretar o conteúdo
    # como um tipo MIME diferente do informado.
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


# ==========================================================
# ROTAS
# ==========================================================

app.include_router(auth_router)
app.include_router(consulta_router)
app.include_router(paciente_router)
app.include_router(profissional_router)
app.include_router(admin_router)


# ==========================================================
# BANCO DE DADOS
# ==========================================================

@app.on_event("startup")
def on_startup():
    if os.getenv("TESTING") != "1":
        create_db_and_tables()


# ==========================================================
# HEALTHCHECK
# ==========================================================

@app.get("/", tags=["Healthcheck"])
def healthcheck():
    return {
        "status": "ok",
        "mensagem": "API de agendamento online e segura"
    }