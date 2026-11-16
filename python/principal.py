"""Ponto de entrada do trabalho: junta os tres paradigmas.

Fluxo:
  1) le o mapa e o pedido (JSON);
  2) valida o contrato (contrato.py);
  3) usa o Prolog para a rota Base -> cada destino (paradigma logico);
  4) usa o Lisp para a melhor ordem de entrega (paradigma funcional);
  5) usa o Dijkstra em Python para calcular o percurso total e o
     plano final, incluindo verificacao de carga e autonomia.

Uso:
    python python/principal.py --entrada dados/pedido_exemplo.json
    python python/principal.py --entrada dados/pedido_exemplo.json --sem-externos
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

import coord_lisp  # noqa: E402
import coord_prolog  # noqa: E402
import contrato  # noqa: E402
from dijkstra import custo_do_percurso, menor_caminho  # noqa: E402
from grafo import Grafo  # noqa: E402
from veiculo import criar_veiculo  # noqa: E402


def carregar(caminho: Path) -> Dict[str, Any]:
    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def plano_de_rota(
    grafo: Grafo,
    base: str,
    sequencia: List[str],
    pesos: Dict[str, float],
) -> Dict[str, Any]:
    """Monta o percurso completo (base -> paradas -> base) com Dijkstra."""
    ordem = [base] + list(sequencia) + [base]
    percurso: List[str] = [ordem[0]]
    total = 0.0
    trechos: List[Dict[str, Any]] = []

    for origem, destino in zip(ordem, ordem[1:]):
        custo, caminho = menor_caminho(grafo, origem, destino, pesos)
        if not caminho:
            return {"viavel": False, "motivo": f"sem caminho entre {origem} e {destino}"}
        total += custo
        percurso.extend(caminho[1:])
        trechos.append({"de": origem, "para": destino, "custo": custo, "caminho": caminho})

    return {
        "viaivel": True,
        "percurso": percurso,
        "trechos": trechos,
        "custo_total": round(total, 2),
    }


def executar(entrada: Path, mapa: Path, usar_externos: bool = True) -> Dict[str, Any]:
    dados_mapa = carregar(mapa)
    pedido = carregar(entrada)

    contrato.validar_mapa(dados_mapa)
    contrato.validar_pedido(pedido)

    grafo = Grafo.de_dicionario(dados_mapa)
    pesos = pedido.get("pesos_custo", {"distancia": 1.0})
    base = pedido["base"]
    entregas = pedido["entregas"]
    veiculo = criar_veiculo(
        pedido["veiculo"]["tipo"],
        float(pedido["veiculo"]["capacidade_kg"]),
        float(pedido["veiculo"]["autonomia_km"]),
    )

    # (a) cada destino precisa existir no mapa
    destinos = [e["destino"] for e in entregas]
    for destino in destinos:
        if not grafo.possui(destino):
            raise contrato.ContratoInvalido(f"destino desconhecido no mapa: {destino}")

    # (b) conferencia logica com o Prolog: existe rota base -> destino?
    conferencia: List[Dict[str, Any]] = []
    for destino in destinos:
        custo_py, _ = menor_caminho(grafo, base, destino, pesos)
        item: Dict[str, Any] = {"destino": destino, "custo_python": custo_py}
        if usar_externos and coord_prolog.disponivel():
            resposta = coord_prolog.rota_menor_custo(base, destino, dados_mapa["arestas"])
            item["rota_prolog"] = resposta["rota"]
            item["custo_prolog"] = resposta["custo"]
            item["concorda"] = abs(resposta["custo"] - custo_py) < 1e-6
        conferencia.append(item)

    # (c) melhor ordem de entrega: Lisp quando disponivel, senao heuristica
    if usar_externos:
        resposta_lisp = coord_lisp.otimizar_sequencia(
            base=base,
            arestas=dados_mapa["arestas"],
            entregas=entregas,
            pesos_custo=pesos,
        )
        sequencia = resposta_lisp["sequencia"]
        origem_ordem = "lisp"
    else:
        sequencia = heuristica_por_prioridade(entregas)
        origem_ordem = "heuristica-python"

    plano = plano_de_rota(grafo, base, sequencia, pesos)

    # (d) tarifas de negocio: carga e autonomia
    peso_total = sum(float(e["peso_kg"]) for e in entregas)
    distancia = custo_do_percurso(
        grafo, plano["percurso"], {"distancia": 1.0, "risco": 0.0, "pedagio": 0.0}
    ) if plano["viaivel"] else float("inf")

    return {
        "veiculo": veiculo.descricao(),
        "peso_total_kg": peso_total,
        "carga_ok": veiculo.cabe(peso_total),
        "distancia_km": distancia,
        "autonomia_ok": distancia <= veiculo.autonomia_km,
        "litros": veiculo.litros_para(distancia) if distancia != float("inf") else None,
        "origem_da_ordem": origem_ordem,
        "sequencia": sequencia,
        "plano": plano,
        "conferencia_prolog": conferencia,
        "prioridades": ordenar_prioridades(entregas),
    }


def heuristica_por_prioridade(entregas: List[Dict[str, Any]]) -> List[str]:
    """Plano B sem Lisp: prioridade primeiro, mais pesado depois."""
    ordenadas = sorted(entregas, key=lambda e: (e.get("prioridade", 0), -float(e["peso_kg"])))
    return [e["destino"] for e in ordenadas]


def ordenar_prioridades(entregas: List[Dict[str, Any]]) -> List[str]:
    ordenadas = sorted(entregas, key=lambda e: (e.get("prioridade", 0), e["id"]))
    return [e["id"] for e in ordenadas]


def formatar_relatorio(resultado: Dict[str, Any]) -> str:
    linhas = [
        "=" * 62,
        "RELATORIO DO PLANO DE ENTREGAS",
        "=" * 62,
        f"Veiculo................: {resultado['veiculo']}",
        f"Peso total.............: {resultado['peso_total_kg']:.0f} kg"
        f" ({'cabe' if resultado['carga_ok'] else 'EXCEDE a capacidade'})",
        f"Distancia do percurso..: {resultado['distancia_km']:.1f} km",
        f"Autonomia..............: {'ok' if resultado['autonomia_ok'] else 'INSUFICIENTE'}"
        f" ({resultado['litros']} litros estimados)",
        f"Ordem obtida por......: {resultado['origem_da_ordem']}",
        f"Ordem das prioridades..: {', '.join(resultado['prioridades'])}",
        "",
        "Percurso:",
        "  " + " -> ".join(resultado["plano"].get("percurso", [])),
        "",
        "Trechos:",
    ]
    for trecho in resultado["plano"].get("trechos", []):
        linhas.append(
            f"  {trecho['de']:>8} -> {trecho['para']:<8} custo {trecho['custo']:>7.2f}"
            f"  via {', '.join(trecho['caminho'])}"
        )
    linhas.append("")
    linhas.append("Conferencia logica (Prolog x Python):")
    for item in resultado["conferencia_prolog"]:
        if "custo_prolog" in item:
            marca = "OK" if item["concorda"] else "DIVERGE"
            linhas.append(
                f"  {item['destino']:<8} python={item['custo_python']:>7.2f}"
                f" prolog={item['custo_prolog']:>7.2f}  -> {marca}"
            )
        else:
            linhas.append(f"  {item['destino']:<8} python={item['custo_python']:>7.2f} (prolog fora)")
    linhas.append("=" * 62)
    return "\n".join(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plano de entregas com Python, Prolog e Lisp")
    parser.add_argument("--entrada", default=str(RAIZ / "dados" / "pedido_exemplo.json"))
    parser.add_argument("--mapa", default=str(RAIZ / "dados" / "mapa.json"))
    parser.add_argument(
        "--sem-externos",
        action="store_true",
        help="roda so com Python (util quando Prolog/Lisp nao estao instalados)",
    )
    parser.add_argument("--json", action="store_true", help="imprime a saida em JSON")
    args = parser.parse_args()

    try:
        resultado = executar(Path(args.entrada), Path(args.mapa), not args.sem_externos)
    except (contrato.ContratoInvalido, coord_prolog.PrologIndisponivel, coord_lisp.LispIndisponivel) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    except FileNotFoundError as erro:
        print(f"Arquivo nao encontrado: {erro.filename}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print(formatar_relatorio(resultado))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
