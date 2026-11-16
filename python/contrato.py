"""Contrato JSON trocado entre o Python e os modulos Prolog/Lisp.

Centralizar aqui evita que cada modulo invente o seu formato.
Todas as funcoes levantam ContratoInvalido com mensagem em portugues.
"""

from __future__ import annotations

from typing import Any, Dict, List

CAMPOS_ARESTA = {"origem", "destino", "distancia"}
CAMPOS_ENTREGA = {"id", "destino", "peso_kg"}


class ContratoInvalido(ValueError):
    """Erro de formato nos dados de entrada ou na resposta dos modulos."""


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise ContratoInvalido(mensagem)


def validar_pedido(pedido: Dict[str, Any]) -> None:
    _exigir(isinstance(pedido, dict), "o pedido deve ser um objeto JSON")
    for chave in ("base", "veiculo", "entregas"):
        _exigir(chave in pedido, f"campo obrigatorio ausente no pedido: {chave}")

    veiculo = pedido["veiculo"]
    _exigir(isinstance(veiculo, dict), "'veiculo' deve ser um objeto")
    _exigir(veiculo.get("tipo") in {"moto", "van"}, "'veiculo.tipo' deve ser 'moto' ou 'van'")
    _exigir(float(veiculo.get("capacidade_kg", 0)) > 0, "'veiculo.capacidade_kg' deve ser positiva")

    entregas: List[Dict[str, Any]] = pedido["entregas"]
    _exigir(isinstance(entregas, list) and entregas, "'entregas' deve ser uma lista nao vazia")
    vistos = set()
    for entrega in entregas:
        _exigir(isinstance(entrega, dict), "cada entrega deve ser um objeto")
        faltando = CAMPOS_ENTREGA - set(entrega)
        _exigir(not faltando, f"entrega sem os campos: {sorted(faltando)}")
        _exigir(entrega["id"] not in vistos, f"id de entrega repetido: {entrega['id']}")
        vistos.add(entrega["id"])
        _exigir(float(entrega["peso_kg"]) > 0, f"peso invalido na entrega {entrega['id']}")


def validar_mapa(mapa: Dict[str, Any]) -> None:
    _exigir(isinstance(mapa, dict), "o mapa deve ser um objeto JSON")
    arestas = mapa.get("arestas")
    _exigir(isinstance(arestas, list) and arestas, "'arestas' deve ser uma lista nao vazia")
    for aresta in arestas:
        faltando = CAMPOS_ARESTA - set(aresta)
        _exigir(not faltando, f"aresta sem os campos: {sorted(faltando)}")
        _exigir(float(aresta["distancia"]) > 0, "distancia da aresta deve ser positiva")


def validar_resposta_rota(resposta: Dict[str, Any]) -> None:
    """Resposta esperada do Prolog: {"rota": [...], "custo": numero}."""
    _exigir(isinstance(resposta, dict), "resposta do Prolog deve ser objeto")
    _exigir(isinstance(resposta.get("rota"), list), "resposta do Prolog sem lista 'rota'")
    _exigir("custo" in resposta, "resposta do Prolog sem campo 'custo'")


def validar_resposta_sequencia(resposta: Dict[str, Any]) -> None:
    """Resposta esperada do Lisp: {"sequencia": [...], "custo": numero}."""
    _exigir(isinstance(resposta, dict), "resposta do Lisp deve ser objeto")
    _exigir(isinstance(resposta.get("sequencia"), list), "resposta do Lisp sem lista 'sequencia'")
    _exigir("custo" in resposta, "resposta do Lisp sem campo 'custo'")
