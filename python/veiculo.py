"""Hierarquia de veiculos (heranca e polimorfismo)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Veiculo(ABC):
    """Classe abstrata: todo veiculo carrega peso e gasta combustivel."""

    def __init__(self, capacidade_kg: float, autonomia_km: float, consumo_km_por_l: float = 10.0):
        if capacidade_kg <= 0 or autonomia_km <= 0:
            raise ValueError("capacidade e autonomia devem ser positivas")
        self._capacidade_kg = float(capacidade_kg)
        self._autonomia_km = float(autonomia_km)
        self._consumo_km_por_l = float(consumo_km_por_l)

    @property
    def capacidade_kg(self) -> float:
        return self._capacidade_kg

    @property
    def autonomia_km(self) -> float:
        return self._autonomia_km

    @abstractmethod
    def descricao(self) -> str:
        """Texto curto usado no relatorio de saida."""

    def cabe(self, peso_total: float) -> bool:
        return peso_total <= self._capacidade_kg

    def litros_para(self, km: float) -> float:
        return round(km / self._consumo_km_por_l, 2)


class Moto(Veiculo):
    def __init__(self) -> None:
        super().__init__(capacidade_kg=30, autonomia_km=120, consumo_km_por_l=35)

    def descricao(self) -> str:
        return "moto (entregas leves)"


class Van(Veiculo):
    def __init__(self, capacidade_kg: float = 800, autonomia_km: float = 60) -> None:
        super().__init__(capacidade_kg=capacidade_kg, autonomia_km=autonomia_km, consumo_km_por_l=9)

    def descricao(self) -> str:
        return f"van {int(self._capacidade_kg)} kg"


def criar_veiculo(tipo: str, capacidade_kg: float, autonomia_km: float) -> Veiculo:
    """Fabrica simples que traduz o JSON de entrada em objeto Veiculo."""
    tipo = tipo.strip().lower()
    if tipo == "moto":
        return Moto()
    if tipo == "van":
        return Van(capacidade_kg=capacidade_kg, autonomia_km=autonomia_km)
    raise ValueError(f"tipo de veiculo desconhecido: {tipo}")
