from datetime import datetime, timezone
from pathlib import Path


IAST_LOG_FILE = Path("iast-runtime.log")


def registrar_evento_iast(
    metodo: str,
    caminho: str,
    status_code: int,
    observacao: str = ""
):
    """
    Instrumentação simplificada de runtime para evidenciar
    requisições exercitadas durante os testes de segurança.
    """

    timestamp = datetime.now(timezone.utc).isoformat()

    linha = (
        f"{timestamp} | "
        f"{metodo} | "
        f"{caminho} | "
        f"status={status_code}"
    )

    if observacao:
        linha += f" | {observacao}"

    with IAST_LOG_FILE.open("a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def limpar_log_iast():
    """
    Remove o log anterior antes de uma nova execução de testes.
    """

    if IAST_LOG_FILE.exists():
        IAST_LOG_FILE.unlink()