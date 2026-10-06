from fastapi import APIRouter, Depends
from models.usuario import Usuario, PapelUsuario
from security import exigir_papel

router = APIRouter(prefix="/admin", tags=["Administração"])

@router.get("/relatorio-sistema", dependencies=[Depends(exigir_papel(PapelUsuario.ADMIN))])
def visualizar_relatorio_sistema():
    return {"status": "sucesso", "dados": "Relatório confidencial do sistema"}

