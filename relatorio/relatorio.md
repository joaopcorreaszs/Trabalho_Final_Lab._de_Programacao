# Relatório — Trabalho Final de Laboratório de Programação

**Tema:** Opção 1 — Logística e Rotas
**Integração de paradigmas:** Python (orientado a objetos), Prolog (lógico) e Common Lisp (funcional)

---

## 1. Problema escolhido

Uma distribuidora precisa planejar a rota de um veículo que sai de uma base,
visita todos os pontos de entrega e retorna à base, gastando o mínimo possível.
O custo de cada trecho não é só a distância: também pesam o risco da via e o
pedágio. Além disso, a solução precisa respeitar duas regras de negócio:

1. o peso total das entregas não pode passar da capacidade do veículo;
2. a distância total não pode passar da autonomia do veículo.

O problema tem três partes naturais, e cada uma cai bem em um paradigma:

| Parte | Paradigma | Por quê |
|---|---|---|
| Representar o mapa e as entregas | OO (Python) | entidades com estado e comportamento |
| Descobrir se existe rota e conferir regras | Lógico (Prolog) | fatos e regras de inferência |
| Achar a melhor ordem de visita | Funcional (Lisp) | permutações e funções puras |
| Orquestrar e calcular menores caminhos | OO (Python) | Dijkstra e integração |

---

## 2. Arquitetura

```
dados/*.json  ──►  contrato.py (validação)
                        │
                        ▼
                 principal.py  ◄── grafo.py / dijkstra.py / veiculo.py
                   │        │
        ┌──────────┘        └──────────┐
        ▼                              ▼
 coord_prolog.py                 coord_lisp.py
 (processo externo)              (processo externo)
        ▼                              ▼
 prolog/logistica.pl            lisp/nucleo.lisp
```

A fronteira entre os módulos é sempre **JSON** (uma linha na entrada e uma na
saída). Assim, cada módulo pode ser testado isoladamente e o Python não fica
preso a uma biblioteca de integração.

### Contrato de entrada (Python → Prolog)

```json
{"origem":"Base","destino":"Porto",
 "arestas":[{"origem":"Base","destino":"Centro","distancia":8}]}
```

Resposta:

```json
{"ok":true,"rota":["Base","Centro","Porto"],"custo":14}
```

### Contrato de entrada (Python → Lisp)

```json
{"base":"Base",
 "arestas":[{"origem":"Base","destino":"Centro","distancia":8,"risco":2,"pedagio":0}],
 "entregas":[{"id":"E1","destino":"Porto","peso_kg":120,"prioridade":3}],
 "pesos_custo":{"distancia":1.0,"risco":2.0,"pedagio":3.0}}
```

Resposta:

```json
{"sequencia":["Centro","Bosque","Porto","Serra"],"custo":42.0,
 "ordem_por_prioridade":["E2","E3","E4","E1"]}
```

---

## 3. Módulo Python — orientação a objetos

- **`grafo.py`** — classes `No`, `Aresta` e `Grafo`. A lista de adjacência fica
  encapsulada (`_adjacencia`); quem usa o grafo só acessa métodos públicos. As
  arestas valem nos dois sentidos, então `adicionar_aresta` cria também a
  aresta reversa.
- **`dijkstra.py`** — menor caminho com `heapq` (fila de prioridade). Retorna o
  custo e a lista de nós; também há `custo_do_percurso` para o percurso inteiro.
- **`veiculo.py`** — hierarquia com classe abstrata `Veiculo` e subclasses
  `Moto` e `Van` (herança e polimorfismo), mais uma fábrica `criar_veiculo`
  que traduz o JSON em objeto.
- **`contrato.py`** — validação centralizada, com exceção própria
  `ContratoInvalido`.
- **`principal.py`** — orquestrador: valida, chama Prolog e Lisp, monta o
  percurso com Dijkstra e aplica as regras de carga e autonomia.

**Complexidade:** Dijkstra com heap é O((V + E) log V).

### Trecho de destaque — custo ponderado

```python
def custo(self, pesos):
    return (pesos.get("distancia", 1.0) * self.distancia
            + pesos.get("risco", 0.0) * self.risco
            + pesos.get("pedagio", 0.0) * self.pedagio)
```

O mesmo algoritmo serve para "rota mais curta" ou "rota mais segura" apenas
trocando os pesos — argumento de extensibilidade do paradigma OO.

---

## 4. Módulo Prolog — paradigma lógico

- Fatos `trecho(Origem, Destino, Custo)` são **carregados dinamicamente** a
  partir do JSON (`carregar_arestas/1` com `retractall` + `assertz`).
- `rota_menor_custo/4` faz **busca em profundidade com poda por custo**
  (*branch and bound*): explora os vizinhos não visitados (`memberchk` evita
  ciclos) e só continua por um ramo se o custo acumulado já for menor que o
  melhor encontrado até então.
- Regras de negócio declarativas:
  `autonomia_suficiente/3` e `carga_cabe/3`.
- `existe_caminho/3` mostra a busca em profundidade pura, sem custo.
- Saída pelo `library(http/json)` do SWI-Prolog, com `json_write_dict`.

Diferença de estilo em relação ao Python: aqui não dizemos *como* percorrer o
grafo, apenas descrevemos *o que* é um trecho e *o que* é um caminho válido; o
motor de inferência faz a busca.

---

## 5. Módulo Lisp — paradigma funcional

- **Leitor JSON próprio** (`ler-json`), recursivo e sem bibliotecas externas,
  porque o objetivo é demonstrar recursão e funções puras.
- **Merge sort recursivo** (`ordenar-por-prioridade`) para ordenar entregas por
  urgência, sem usar `sort` da linguagem.
- **Permutações puras** (`permutacoes` + `inserir-todas`): a lista não é
  alterada, cada chamada devolve uma lista nova. Combina com `mapcar` e
  `reduce`, típicos do paradigma funcional.
- **Custo por `reduce` e recursão** (`custo-percurso`), somando trechos até o
  percurso fechar no ponto base.
- Para 4 entregas são 24 permutações; o custo é O(n!) e por isso o módulo é
  usado apenas para a **ordem** das paradas, enquanto o Dijkstra em Python
  traça o caminho real dentro do grafo.

### Trecho de destaque

```lisp
(defun permutacoes (lista)
  (if (null lista)
      (list nil)
      (reduce #'append
              (mapcar (lambda (p) (inserir-todas (first lista) p))
                      (permutacoes (cdr lista))))))
```

Função pura: para a mesma entrada, sempre a mesma saída, sem efeitos colaterais.

---

## 6. Integração e testes

- **`coord_prolog.py`** e **`coord_lisp.py`** executam os interpretadores como
  processo externo (`swipl` e `sbcl`), escrevendo JSON no `stdin` e lendo uma
  linha do `stdout`. Vantagem: não exige bibliotecas de integração.
- A saída de cada módulo passa por `validar_resposta_rota` /
  `validar_resposta_sequencia` antes de ser usada — falha cedo em vez de
  produzir resultado errado silenciosamente.
- O relatório final mostra uma **conferência cruzada**: o custo calculado pelo
  Prolog é comparado com o do Dijkstra em Python. Se divergirem, aparece
  `DIVERGE`, o que serviu como teste de equivalência dos dois algoritmos.
- Testes automatizados em `python/testes/test_nucleo.py` (unittest): grafo
  bidirecional, custo ponderado, escolha do caminho mais barato, origem igual
  ao destino, grafo desconexo, capacidade do veículo, validação de contrato e
  id repetido.

Execução:

```powershell
python -m unittest discover -s python/testes -v
python python/principal.py --entrada dados/pedido_exemplo.json
python python/principal.py --entrada dados/pedido_exemplo.json --sem-externos
```

---

## 7. Como o mesmo problema apareceria em cada paradigma

| Aspecto | Python (OO) | Prolog (lógico) | Lisp (funcional) |
|---|---|---|---|
| Ideia central | objetos que colaboram | fatos e regras | funções que se compõem |
| Estado | explícito nos atributos | banco de fatos dinâmico | quase ausente |
| Repetição | laços e `heapq` | backtracking do motor | recursão |
| Erro comum | efeito colateral | falha silenciosa da consulta | função impura quebrando a composição |
| Ponto forte | legibilidade e bibliotecas | regras declarativas | transformação de listas |

---

## 8. Limitações e trabalhos futuros

- A busca da melhor ordem no Lisp é fatorial; para muitas entregas seria
  preciso trocar por heurística (vizinho mais próximo + 2-opt).
- O Prolog hoje confere rotas par a par; poderia receber a lista inteira e
  resolver a ordenação também de forma declarativa.
- A autonomia é checada no total do percurso; uma evolução natural é incluir
  pontos de recarga intermediários.

---

## 9. Conclusão

Os três módulos resolvem partes diferentes do mesmo problema e conversam por
um contrato JSON explícito. O exercício mostra que a escolha do paradigma não é
estética: regras de negócio ficam mais curtas e verificáveis em Prolog,
transformações de listas ficam mais claras em Lisp, e a organização de
entidades e a integração se beneficiam da orientação a objetos em Python.
