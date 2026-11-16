"""Ponte entre o Python e o modulo Prolog (SWI-Prolog).

Duas formas de uso:
  1) pyswip, quando a biblioteca esta instalada (integracao nativa);
  2) processo externo com o SWI-Prolog, que e' o caminho padrao e nao
     exige bibliotecas extras.

O contrato de dados esta em contrato.py.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from contrato import ContratoInvalido, validar_resposta_rota

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_PL = RAIZ / "prolog" / "logistica.pl"


class PrologIndisponivel(RuntimeError):
    """Levantado quando o SWI-Prolog nao esta instalado."""


def _executavel() -> str:
    for nome in ("swipl", "swipl.exe"):
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    raise PrologIndisponivel(
        "SWI-Prolog nao encontrado. Instale o SWI-Prolog para rodar o modulo logico."
    )


def rota_menor_custo(
    origem: str,
    destino: str,
    arestas: list,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Executa o modulo Prolog e devolve {"rota": [...], "custo": numero}.

    Usa processo externo: uma linha JSON no stdin, uma linha no stdout.
    """
    entrada = {
        "origem": origem,
        "destino": destino,
        "arestas": [
            {
                "origem": a["origem"],
                "destino": a["destino"],
                "distancia": float(a["distancia"]),
            }
            for a in arestas
        ],
    }
    processo = subprocess.run(
        [_executavel(), "-q", "-s", str(ARQUIVO_PL), "-g", "main", "-t", "halt"],
        input=json.dumps(entrada, ensure_ascii=False) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if processo.returncode != 0:
        raise ContratoInvalido(f"SWI-Prolog terminou com erro: {processo.stderr.strip()}")

    linha = next((l for l in processo.stdout.splitlines() if l.strip().startswith("{")), "")
    if not linha:
        raise ContratoInvalido("o Prolog nao devolveu JSON")

    resposta = json.loads(linha)
    if resposta.get("erro") or resposta.get("mensagem"):
        raise ContratoInvalido(f"erro no modulo Prolog: {resposta}")
    if not resposta.get("ok", False):
        raise ContratoInvalido(f"sem rota entre {origem} e {destino}")
    validar_resposta_rota(resposta)
    return {"rota": resposta["rota"], "custo": float(resposta["custo"])}


def disponivel() -> bool:
    return shutil.which("swipl") is not None or shutil.which("swipl.exe") is not None
