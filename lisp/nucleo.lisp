;;;; =====================================================================
;;;; nucleo.lisp — modulo do paradigma FUNCIONAL
;;;; Trabalho Final: Logistica e rotas (Opcao 1)
;;;;
;;;; Responsabilidades:
;;;;   1) Ler um pedido em JSON (sem bibliotecas externas).
;;;;   2) Ordenar entregas por prioridade usando ordenacao propria
;;;;      (merge sort recursivo, sem usar a 'sort' da linguagem).
;;;;   3) Calcular o custo acumulado de uma sequencia de paradas
;;;;      com recursao e funcoes de alta ordem (reduce).
;;;;   4) Gerar e comparar permutacoes via funcoes puras, achando a
;;;;      ordem de visita de menor custo.
;;;;   5) Responder JSON com a sequencia otima.
;;;;
;;;; Uso:  sbcl --script lisp/nucleo.lisp < dados/lisp_entrada.json
;;;; =====================================================================

;;; ---------------------------------------------------------------------
;;; 1. Utilitarios de texto: leitura de JSON minima
;;; ---------------------------------------------------------------------

(defun espaco-branco-p (c)
  (member c '(#\Space #\Tab #\Newline #\Return)))

(defun pular-espacos (texto pos)
  (if (and (< pos (length texto)) (espaco-branco-p (char texto pos)))
      (pular-espacos texto (1+ pos))
      pos))

(defun ler-texto (texto pos)
  "Le uma string JSON a partir da aspa em POS. Devolve (texto . proxima-pos)."
  (let ((fim (position #\" texto :start (1+ pos))))
    (unless fim (error "JSON malformado: texto sem aspas de fechamento"))
    (values (subseq texto (1+ pos) fim) (1+ fim))))

(defun ler-numero (texto pos)
  (let ((fim pos))
    (loop while (and (< fim (length texto))
                     (or (digit-char-p (char texto fim))
                         (member (char texto fim) '(#\- #\. #\e #\E #\+))))
          do (incf fim))
    (values (read-from-string (subseq texto pos fim)) fim)))

(defun ler-valor (texto pos)
  (let ((p (pular-espacos texto pos)))
    (cond
      ((char= (char texto p) #\") (ler-texto texto p))
      ((char= (char texto p) #\{) (ler-objeto texto (1+ p)))
      ((char= (char texto p) #\[) (ler-vetor texto (1+ p)))
      ((char= (char texto p) #\t) (values t (+ p 4)))
      ((char= (char texto p) #\f) (values nil (+ p 5)))
      (t (ler-numero texto p)))))

(defun ler-objeto (texto pos)
  "Devolve uma alist ((\"chave\" . valor) ...)."
  (let ((p (pular-espacos texto pos)))
    (if (char= (char texto p) #\})
        (values nil (1+ p))
        (multiple-value-bind (chave p1) (ler-texto texto p)
          (let ((p2 (pular-espacos texto (1+ (pular-espacos texto p1)))))
            (multiple-value-bind (valor p3) (ler-valor texto p2)
              (let ((p4 (pular-espacos texto p3)))
                (if (char= (char texto p4) #\,)
                    (multiple-value-bind (resto p5) (ler-objeto texto (1+ p4))
                      (values (cons (cons chave valor) resto) p5))
                    (values (list (cons chave valor)) (1+ p4))))))))))

(defun ler-vetor (texto pos)
  (let ((p (pular-espacos texto pos)))
    (if (char= (char texto p) #\])
        (values nil (1+ p))
        (multiple-value-bind (valor p1) (ler-valor texto p)
          (let ((p2 (pular-espacos texto p1)))
            (if (char= (char texto p2) #\,)
                (multiple-value-bind (resto p3) (ler-vetor texto (1+ p2))
                  (values (cons valor resto) p3))
                (values (list valor) (1+ p2))))))))

(defun ler-json (texto)
  "Le a primeira linha inteira como JSON."
  (multiple-value-bind (valor _) (ler-valor texto 0)
    (declare (ignore _))
    valor))

(defun campo (alist chave &optional padrao)
  (let ((par (assoc chave alist :test #'string=)))
    (if par (cdr par) padrao)))

;;; ---------------------------------------------------------------------
;;; 2. Ordenacao por prioridade: merge sort recursivo
;;; ---------------------------------------------------------------------

(defun menor-prioridade (a b)
  "Prioridade menor = mais urgente."
  (< (campo a "prioridade" 0) (campo b "prioridade" 0)))

(defun juntar (esquerda direita)
  "Intercala duas listas ja ordenadas (recursao)."
  (cond
    ((null esquerda) direita)
    ((null direita) esquerda)
    ((menor-prioridade (car esquerda) (car direita))
     (cons (car esquerda) (juntar (cdr esquerda) direita)))
    (t (cons (car direita) (juntar esquerda (cdr direita))))))

(defun dividir (lista)
  "Divide a lista em duas metades iguais."
  (let ((metade (floor (length lista) 2)))
    (values (subseq lista 0 metade) (subseq lista metade))))

(defun ordenar-por-prioridade (lista)
  "Merge sort: caso base de 0 ou 1 elemento, senao divide e junta."
  (if (< (length lista) 2)
      lista
      (multiple-value-bind (esquerda direita) (dividir lista)
        (juntar (ordenar-por-prioridade esquerda)
                (ordenar-por-prioridade direita)))))

;;; ---------------------------------------------------------------------
;;; 3. Custo de uma sequencia de paradas
;;; ---------------------------------------------------------------------

(defun trecho-entre (mapa origem destino)
  "Procura o trecho entre dois pontos na lista de arestas; NIL se nao existe."
  (find-if (lambda (aresta)
             (or (and (string= (campo aresta "origem") origem)
                      (string= (campo aresta "destino") destino))
                 (and (string= (campo aresta "origem") destino)
                      (string= (campo aresta "destino") origem))))
           mapa))

(defun custo-trecho (aresta pesos)
  (+ (* (campo pesos "distancia" 1.0) (campo aresta "distancia" 0))
     (* (campo pesos "risco" 0.0) (campo aresta "risco" 0))
     (* (campo pesos "pedagio" 0.0) (campo aresta "pedagio" 0))))

(defun custo-percurso (mapa pesos ponto)
  "Custo total do percurso; usa reduce e recursao sobre a lista."
  (if (or (null ponto) (null (cdr ponto)))
      0
      (let ((aresta (trecho-entre mapa (first ponto) (second ponto))))
        (if aresta
            (+ (custo-trecho aresta pesos) (custo-percurso mapa pesos (cdr ponto)))
            most-positive-double-float))))

;;; ---------------------------------------------------------------------
;;; 4. Permutacoes puras e busca da melhor ordem
;;; ---------------------------------------------------------------------

(defun inserir-todas (item lista)
  "Insere ITEM em todas as posicoes possiveis de LISTA (funcao pura)."
  (if (null lista)
      (list (list item))
      (cons (cons item lista)
            (mapcar (lambda (resto) (cons (first lista) resto))
                    (inserir-todas item (cdr lista))))))

(defun permutacoes (lista)
  (if (null lista)
      (list nil)
      (reduce #'append
              (mapcar (lambda (p) (inserir-todas (first lista) p))
                      (permutacoes (cdr lista))))))

(defun melhor-ordem (mapa pesos base entregas)
  "Testa todas as permutacoes e devolve (custo . sequencia)."
  (let* ((destinos (mapcar (lambda (e) (campo e "destino")) entregas))
         (rotas (mapcar (lambda (ordem)
                          (cons ordem
                                (custo-percurso mapa pesos
                                                (append (list base) ordem (list base)))))
                        (permutacoes destinos)))
         (ordenadas (sort (copy-list rotas)
                          (lambda (a b) (< (cdr a) (cdr b))))))
    (first ordenadas)))

;;; ---------------------------------------------------------------------
;;; 5. Saida JSON
;;; ---------------------------------------------------------------------

(defun escrever-json-texto (texto)
  (format t "\"~a\"" texto))

(defun escrever-lista (itens &key (conversor #'escrever-json-texto))
  (format t "[")
  (loop for item in itens
        for primeiro = t then nil
        do (unless primeiro (format t ", "))
           (funcall conversor item))
  (format t "]"))

(defun converter-bool (texto)
  (cond ((equal texto "t") t)
        ((equal texto "f") nil)
        (t texto)))

(defun escrever-json (ordem custo prioridades)
  (format t "{\"sequencia\": ")
  (escrever-lista ordem :conversor #'converter-bool)
  (format t ", \"custo\": ~,2f, \"ordem_por_prioridade\": " custo)
  (escrever-lista prioridades :conversor #'converter-bool)
  (format t "}~%"))

;;; ---------------------------------------------------------------------
;;; 6. Programa principal
;;; ---------------------------------------------------------------------

(defun ler-tudo (fluxo)
  (let ((linhas '()))
    (loop for linha = (read-line fluxo nil nil)
          while linha
          do (push linha linhas))
    (format nil "~{~a~}" (nreverse linhas))))

(defun principal (&optional (fluxo *standard-input*))
  (handler-case
      (let* ((dados (ler-json (ler-tudo fluxo)))
             (base (campo dados "base"))
             (mapa (campo dados "arestas"))
             (pesos (campo dados "pesos_custo" nil))
             (entregas (campo dados "entregas")))
        (if (or (null entregas) (null mapa))
            (format t "{\"erro\": \"entrada sem entregas ou arestas\"}~%")
            (let* ((ordenadas (ordenar-por-prioridade entregas))
                   (prioridades (mapcar (lambda (e) (campo e "id")) ordenadas))
                   (melhor (melhor-ordem mapa pesos base entregas)))
              (escrever-json (cdr melhor) (car melhor) prioridades))))
    (error (e)
      (format t "{\"erro\": \"~a\"}~%" e))))

(principal)
