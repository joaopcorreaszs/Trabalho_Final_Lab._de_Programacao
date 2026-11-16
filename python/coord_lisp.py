"""Ponte entre o Python e o modulo Lisp (SBCL).

A comunicacao e' por processo externo: escrevemos o JSON no stdin do
SBCL e lemos uma linha JSON no stdout. Assim os dois paradigmas
ficam realmente independentes.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from contrato import ContratoInvalido, validar_resposta_sequencia

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT_LISP = RAIZ / "lisp" / "nucleo.lisp"


class LispIndisponivel(RuntimeError):
    """Levantado quando o executavel do SBCL nao esta no PATH."""


def _comando() -> str:
    for nome in ("sbcl", "sbcl.exe"):
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    raise LispIndisponivel(
        "SBCL nao encontrado. Instale o Steel Bank Common Lisp para rodar o modulo funcional."
    )


def otimizar_sequencia(
    base: str,
    arestas: list,
    entregas: list,
    pesos_custo: Dict[str, float] | None = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Chama o Lisp e devolve {"sequencia": [...], "custo": numero}.

    Levanta LispIndisponivel se o SBCL nao existir e ContratoInvalido se
    a resposta vier em formato inesperado.
    """
    entrada = {
        "base": base,
        "arestas": arestas,
        "entregas": entregas,
        "pesos_custo": pesos_custo or {"distancia": 1.0},
    }
    processo = subprocess.run(
        [_comando(), "--script", str(SCRIPT_LISP)],
        input=json.dumps(entrada, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if processo.returncode != 0:
        raise ContratoInvalido(f"SBCL terminou com erro: {processo.stderr.strip()}")

    linha = next((l for l in processo.stdout.splitlines() if l.strip().startswith("{")), "")
    if not linha:
        raise ContratoInvalido("o Lisp nao devolveu JSON")

    resposta = json.loads(linha)
    if "erro" in resposta:
        raise ContratoInvalido(f"erro no modulo Lisp: {resposta['erro']}")
    validar_resposta_sequencia(resposta)
    return resposta
