"""Menor caminho com o algoritmo de Dijkstra.

Usa uma fila de prioridade (heapq) para sempre expandir o no de menor
custo acumulado. Trabalha sobre o objeto Grafo definido em grafo.py.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Tuple

from grafo import Grafo

Resultado = Tuple[float, List[str]]


def menor_caminho(
    grafo: Grafo,
    origem: str,
    destino: str,
    pesos: Dict[str, float] | None = None,
) -> Resultado:
    """Devolve (custo_total, lista_de_nos) do menor caminho.

    Se nao houver caminho, devolve (inf, []).
    """
    pesos = pesos or {"distancia": 1.0}
    if not grafo.possui(origem) or not grafo.possui(destino):
        return float("inf"), []

    distancias: Dict[str, float] = {no: float("inf") for no in grafo.nos}
    anteriores: Dict[str, str] = {}
    distancias[origem] = 0.0
    fila: List[Tuple[float, str]] = [(0.0, origem)]
    visitados = set()

    while fila:
        custo_atual, atual = heapq.heappop(fila)
        if atual in visitados:
            continue
        visitados.add(atual)
        if atual == destino:
            break
        for aresta in grafo.vizinhos(atual):
            novo_custo = custo_atual + aresta.custo(pesos)
            if novo_custo < distancias[aresta.destino]:
                distancias[aresta.destino] = novo_custo
                anteriores[aresta.destino] = atual
                heapq.heappush(fila, (novo_custo, aresta.destino))

    if distancias.get(destino, float("inf")) == float("inf"):
        return float("inf"), []

    caminho: List[str] = []
    passo = destino
    while passo != origem:
        caminho.append(passo)
        passo = anteriores[passo]
    caminho.append(origem)
    caminho.reverse()
    return round(distancias[destino], 2), caminho


def custo_do_percurso(
    grafo: Grafo, percurso: List[str], pesos: Dict[str, float] | None = None
) -> float:
    """Custo de seguir a lista de nos na ordem dada (soma de trechos)."""
    pesos = pesos or {"distancia": 1.0}
    total = 0.0
    for a, b in zip(percurso, percurso[1:]):
        achou = next((v for v in grafo.vizinhos(a) if v.destino == b), None)
        if achou is None:
            return float("inf")
        total += achou.custo(pesos)
    return round(total, 2)
