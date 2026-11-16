# Trabalho Final — Logística e Rotas

Integração de três paradigmas de programação:
Python (orientado a objetos, orquestrador), Prolog (lógico) e Common Lisp (funcional).

## Estrutura do projeto

```
.
├── dados/                  grafo, encomendas e pedidos de exemplo (JSON)
├── python/                 orquestrador orientado a objetos
│   ├── grafo.py            classes Grafo, No, Aresta (encapsulamento)
│   ├── dijkstra.py         Dijkstra com fila de prioridade (heapq)
│   ├── veiculo.py          hierarquia Veiculo -> Moto, Van (herança)
│   ├── coord_prolog.py     ponte com SWI-Prolog (pyswip)
│   ├── coord_lisp.py       ponte com SBCL (processo externo)
│   ├── contrato.py         validação do contrato JSON
│   ├── testes/             testes automatizados (unittest)
│   └── principal.py        ponto de entrada
├── prolog/logistica.pl     fatos, regras e busca em profundidade
├── lisp/nucleo.lisp        funções puras, recursão, ordenação e recombinação
└── relatorio/              relatório em Markdown (depois exportar para PDF)
```

## Como rodar

Requisitos: Python 3.10+, SWI-Prolog (com `pyswip`) e SBCL.

```powershell
# 1) testes do módulo Python
python -m unittest discover -s python/testes -v

# 2) execução completa (orquestrador chama Prolog e Lisp)
python python/principal.py --entrada dados/pedido_exemplo.json

# 3) módulos isolados
swipl -q -s prolog/logistica.pl -g main -t halt
sbcl --script lisp/nucleo.lisp
```

## Contrato JSON entre os módulos

O orquestrador envia ao Prolog uma consulta com `origem`, `destino` e a lista
de `arestas`; recebe a rota. Ao Lisp envia a lista de `entregas` e recebe
a sequência otimizada com o custo acumulado. Detalhes no relatório.
