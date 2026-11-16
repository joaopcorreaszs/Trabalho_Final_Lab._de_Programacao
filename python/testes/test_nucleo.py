"""Testes automatizados do modulo Python (unittest).

Rodar a partir da raiz do projeto:
    python -m unittest discover -s python/testes -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

import contrato  # noqa: E402
from dijkstra import custo_do_percurso, menor_caminho  # noqa: E402
from grafo import Aresta, Grafo  # noqa: E402
from veiculo import Moto, Van, criar_veiculo  # noqa: E402

PESOS_SIMPLES = {"distancia": 1.0}


def grafo_triangulo() -> Grafo:
    grafo = Grafo()
    grafo.adicionar_aresta(Aresta("A", "B", 1))
    grafo.adicionar_aresta(Aresta("B", "C", 1))
    grafo.adicionar_aresta(Aresta("A", "C", 5))
    return grafo


class TestGrafo(unittest.TestCase):
    def test_aresta_e_bidirecional(self):
        grafo = grafo_triangulo()
        self.assertEqual(len(grafo.vizinhos("B")), 2)
        self.assertTrue(grafo.possui("C"))

    def test_custo_ponderado(self):
        aresta = Aresta("A", "B", distancia=10, risco=2, pedagio=3)
        pesos = {"distancia": 1.0, "risco": 2.0, "pedagio": 3.0}
        self.assertEqual(aresta.custo(pesos), 10 + 4 + 9)

    def test_vizinhos_de_no_inexistente(self):
        self.assertEqual(grafo_triangulo().vizinhos("Z"), [])


class TestDijkstra(unittest.TestCase):
    def test_escolhe_caminho_mais_barato(self):
        custo, caminho = menor_caminho(grafo_triangulo(), "A", "C", PESOS_SIMPLES)
        self.assertEqual(caminho, ["A", "B", "C"])
        self.assertEqual(custo, 2)

    def test_origem_igual_destino(self):
        custo, caminho = menor_caminho(grafo_triangulo(), "A", "A", PESOS_SIMPLES)
        self.assertEqual((custo, caminho), (0.0, ["A"]))

    def test_sem_caminho(self):
        grafo = Grafo()
        grafo.adicionar_aresta(Aresta("A", "B", 2))
        grafo.adicionar_aresta(Aresta("C", "D", 2))
        custo, caminho = menor_caminho(grafo, "A", "D", PESOS_SIMPLES)
        self.assertEqual(caminho, [])
        self.assertEqual(custo, float("inf"))

    def test_custo_do_percurso(self):
        self.assertEqual(custo_do_percurso(grafo_triangulo(), ["A", "B", "C"]), 2)
        self.assertEqual(
            custo_do_percurso(grafo_triangulo(), ["A", "C", "B"], PESOS_SIMPLES), float("inf")
        )


class TestVeiculo(unittest.TestCase):
    def test_capacidade_da_moto(self):
        self.assertTrue(Moto().cabe(20))
        self.assertFalse(Moto().cabe(50))

    def test_fabrica(self):
        van = criar_veiculo("van", 500, 80)
        self.assertIsInstance(van, Van)
        self.assertIn("van", van.descricao())

    def test_tipo_invalido(self):
        with self.assertRaises(ValueError):
            criar_veiculo("caminhao", 100, 50)

    def test_litros(self):
        self.assertAlmostEqual(Van().litros_para(90), 10.0)


class TestContrato(unittest.TestCase):
    def pedido_valido(self) -> dict:
        return {
            "base": "Base",
            "veiculo": {"tipo": "van", "capacidade_kg": 800, "autonomia_km": 60},
            "entregas": [{"id": "E1", "destino": "Centro", "peso_kg": 10}],
        }

    def test_pedido_ok(self):
        contrato.validar_pedido(self.pedido_valido())

    def test_peso_negativo(self):
        pedido = self.pedido_valido()
        pedido["entregas"][0]["peso_kg"] = -1
        with self.assertRaises(contrato.ContratoInvalido):
            contrato.validar_pedido(pedido)

    def test_id_repetido(self):
        pedido = self.pedido_valido()
        pedido["entregas"].append({"id": "E1", "destino": "Porto", "peso_kg": 5})
        with self.assertRaises(contrato.ContratoInvalido):
            contrato.validar_pedido(pedido)

    def test_resposta_rota_incompleta(self):
        with self.assertRaises(contrato.ContratoInvalido):
            contrato.validar_resposta_rota({"rota": ["A"]})


if __name__ == "__main__":
    unittest.main()
