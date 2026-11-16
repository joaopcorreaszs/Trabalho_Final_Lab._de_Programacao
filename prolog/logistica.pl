/* =====================================================================
   logistica.pl — modulo do paradigma LOGICO
   Trabalho Final: Logistica e rotas (Opcao 1)
   ---------------------------------------------------------------------
   Responsabilidades:
     1) Guardar o mapa como fatos trecho/3 (carregados via JSON).
     2) Achar caminho de menor custo por BUSCA EM PROFUNDIDADE com
        poda por custo (branch and bound).
     3) Aplicar regras de negocio: existencia de rota, autonomia e carga.
     4) Conversar em JSON com o orquestrador Python.
   ---------------------------------------------------------------------
   Uso direto:
       swipl -q -s prolog/logistica.pl -g main -t halt
       (envie uma linha JSON no stdin)
   ===================================================================== */

:- module(logistica, [
       trecho/3,
       carregar_arestas/1,
       rota_menor_custo/4,
       existe_caminho/3,
       autonomia_suficiente/3,
       carga_cabe/3,
       main/0
   ]).

:- use_module(library(http/json)).

:- dynamic trecho/3.

/* ---------------------------------------------------------------------
   1) FATOS
   trecho(Origem, Destino, Custo) vale nos dois sentidos.
   ------------------------------------------------------------------- */

carregar_arestas(Arestas) :-
    retractall(trecho(_, _, _)),
    forall(member(A, Arestas), assert_trecho(A)).

assert_trecho(aresta(O, D, C)) :-
    assertz(trecho(O, D, C)),
    assertz(trecho(D, O, C)).

/* ---------------------------------------------------------------------
   2) BUSCA EM PROFUNDIDADE COM PODA
   rota_menor_custo(+Origem, +Destino, -Rota, -Custo)

   A exploracao parte da origem, empilha nos vizinhos ainda nao
   visitados, e so aceita um caminho quando o custo e' menor que o
   melhor ja encontrado (poda). A lista Visitados evita ciclos.
   ------------------------------------------------------------------- */

rota_menor_custo(Origem, Destino, Rota, Custo) :-
    ( Origem == Destino ->
        Rota = [Origem], Custo = 0.0
    ;
        buscar(Origem, Destino, [Origem], 0.0, inf, MelhorRota, MelhorCusto),
        MelhorCusto \== inf,
        Rota = MelhorRota, Custo = MelhorCusto
    ).

buscar(Atual, Destino, Visitados, CustoAtual, CustoLimite, Rota, Custo) :-
    ( Atual == Destino ->
        Rota = Visitados, Custo = CustoAtual        % achou um caminho completo
    ;
        Rota = RotaFilho, Custo = CustoFilho,
        findall(D-C,
                ( trecho(Atual, D, C), \+ memberchk(D, Visitados) ),
                Vizinhos),
        expandir(Vizinhos, Atual, Destino, Visitados, CustoAtual,
                 CustoLimite, inf, [], RotaFilho, CustoFilho)
    ).

expandir([], _, _, _, _, _, MelhorCusto, MelhorRota, MelhorRota, MelhorCusto) :- !.
expandir([D-C|Resto], Atual, Destino, Visitados, CustoAtual, Limite,
         MelhorCustoAte, MelhorRotaAte, Rota, Custo) :-
    NovoCusto is CustoAtual + C,
    NovoLimite is min(Limite, MelhorCustoAte),
    ( NovoCusto < NovoLimite ->
        ( buscar(D, Destino, [D|Visitados], NovoCusto, NovoLimite, R, K)
        -> ( K < MelhorCustoAte ->
             MelhorCusto1 = K, MelhorRota1 = R
           ; MelhorCusto1 = MelhorCustoAte, MelhorRota1 = MelhorRotaAte )
        ; MelhorCusto1 = MelhorCustoAte, MelhorRota1 = MelhorRotaAte )
    ; MelhorCusto1 = MelhorCustoAte, MelhorRota1 = MelhorRotaAte ),
    expandir(Resto, Atual, Destino, Visitados, CustoAtual, Limite,
             MelhorCusto1, MelhorRota1, Rota, Custo).

/* ---------------------------------------------------------------------
   3) REGRAS DE NEGOCIO
   ------------------------------------------------------------------- */

% existe_caminho(+Origem, +Destino, -Rota) — busca simples, sem custo.
existe_caminho(Origem, Destino, Rota) :-
    caminho(Origem, Destino, [Origem], RotaInvertida),
    reverse(RotaInvertida, Rota).

caminho(Destino, Destino, Acumulado, Acumulado).
caminho(Atual, Destino, Visitados, Rota) :-
    trecho(Atual, Proximo, _),
    \+ memberchk(Proximo, Visitados),
    caminho(Proximo, Destino, [Proximo|Visitados], Rota).

% autonomia_suficiente(+Km, +AutonomiaKm, -Veredito)
autonomia_suficiente(Km, Autonomia, ok) :- Km =< Autonomia, !.
autonomia_suficiente(_, _, insuficiente).

% carga_cabe(+PesoTotal, +Capacidade, -Veredito)
carga_cabe(Peso, Capacidade, ok) :- Peso =< Capacidade, !.
carga_cabe(_, _, excedida).

/* ---------------------------------------------------------------------
   4) INTERFACE JSON
   Entrada esperada (uma linha):
   {"origem":"Base","destino":"Porto","arestas":[{"origem":"Base",
    "destino":"Centro","distancia":8}, ...]}
   Saida:
   {"ok":true,"rota":["Base","Centro","Porto"],"custo":14}
   ------------------------------------------------------------------- */

main :-
    read_line_to_string(user_input, Linha),
    ( Linha == end_of_file -> halt
    ; catch(processar(Linha), Erro,
            ( responder(_{ok:false, erro:Erro}) )),
      halt
    ).

processar(Linha) :-
    atom_string(Atom, Linha),
    atom_json_dict(Atom, Dict, [value_string_as(atom)]),
    Origem = Dict.get("origem"),
    Destino = Dict.get("destino"),
    Arestas = Dict.get("arestas"),
    maplist(aresta_de_dict, Arestas, Fatos),
    carregar_arestas(Fatos),
    ( rota_menor_custo(Origem, Destino, Rota, Custo) ->
        responder(_{ok:true, rota:Rota, custo:Custo})
    ; responder(_{ok:false, rota:[], custo:null, mensagem:"sem rota"})
    ).

aresta_de_dict(D, aresta(O, T, C)) :-
    O = D.get("origem"),
    T = D.get("destino"),
    C = D.get("distancia").

responder(Dict) :-
    current_output(Saida),
    json_write_dict(Saida, Dict, [width(0)]),
    nl(Saida),
    flush_output(Saida).
