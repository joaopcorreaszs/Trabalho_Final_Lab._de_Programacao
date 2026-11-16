"""Estruturas de grafo para o problema de logística.

Aqui ficam as classes do paradigma orientado a objetos:
No, Aresta e Grafo. O grafo e' a base compartilhada pelos modulos
Python, Prolog e Lisp (que recebem a mesma informacao em JSON).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, List


@dataclass(frozen=True)
class No:
    """Um ponto de entrega ou de passagem (cidade, bairro, base)."""

    nome: str

    def __str__(self) -> str:  # pragma: no cover - conveniencia
        return self.nome


@dataclass(frozen=True)
class Aresta:
    """Trecho de via entre dois nos, com atributos usados no custo."""

    origem: str
    destino: str
    distancia: float
    risco: float = 0.0
    pedagio: float = 0.0

    def custo(self, pesos: Dict[str, float]) -> float:
        """Custo ponderado do trecho, segundo os pesos informados."""
        return (
            pesos.get("distancia", 1.0) * self.distancia
            + pesos.get("risco", 0.0) * self.risco
            + pesos.get("pedagio", 0.0) * self.pedagio
        )

    def como_dicionario(self) -> dict:
        return {
            "origem": self.origem,
            "destino": self.destino,
            "distancia": self.distancia,
            "risco": self.risco,
            "pedagio": self.pedagio,
        }


class Grafo:
    """Grafo nao dirigido com pesos, construido a partir de arestas.

    Encapsula a lista de adjacencia: quem usa o grafo nao mexe
    diretamente na estrutura interna.
    """

    def __init__(self) -> None:
        self._adjacencia: Dict[str, List[Aresta]] = {}
        self._arestas: List[Aresta] = []

    # ---------- construcao ----------
    def adicionar_aresta(self, aresta: Aresta) -> None:
        self._adjacencia.setdefault(aresta.origem, []).append(aresta)
        # o trajeto vale nos dois sentidos (ida e volta)
        reversa = Aresta(
            origem=aresta.destino,
            destino=aresta.origem,
            distancia=aresta.distancia,
            risco=aresta.risco,
            pedagio=aresta.pedagio,
        )
        self._adjacencia.setdefault(reversa.origem, []).append(reversa)
        self._arestas.append(aresta)

    @classmethod
    def de_dicionario(cls, dados: dict) -> "Grafo":
        grafo = cls()
        for item in dados.get("arestas", []):
            grafo.adicionar_aresta(
                Aresta(
                    origem=item["origem"],
                    destino=item["destino"],
                    distancia=float(item["distancia"]),
                    risco=float(item.get("risco", 0)),
                    pedagio=float(item.get("pedagio", 0)),
                )
            )
        return grafo

    # ---------- consulta ----------
    @property
    def nos(self) -> List[str]:
        return sorted(self._adjacencia.keys())

    @property
    def arestas(self) -> List[Aresta]:
        return list(self._arestas)

    def vizinhos(self, nome: str) -> List[Aresta]:
        return list(self._adjacencia.get(nome, []))

    def possui(self, nome: str) -> bool:
        return nome in self._adjacencia

    def __iter__(self) -> Iterator[str]:
        return iter(self.nos)

    def __len__(self) -> int:
        return len(self._adjacencia)

    def __repr__(self) -> str:  # pragma: no cover - conveniencia
        return f"Grafo({len(self._adjacencia)} nos, {len(self._arestas)} arestas)"
