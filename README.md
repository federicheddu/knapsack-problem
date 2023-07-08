# **Knapsack Problem**

>  Questo è un progetto svolto nell'ambito degli esami di **Decision Scienze** *(a.k.a. Ricerca Operativa)* e **Network Flow Optimization** del **CdLM in Informatica** presso l'Università degli Studi di Cagliari

| **Studente**          | **Matricola** | **E-Mail**                        |
|-----------------------|---------------|-----------------------------------|
| Federico Meloni       | 60/73/65243   | <f.meloni62@studenti.unica.it>    |
| Luca Faccin           | 60/73/65236   | <l.faccin@studenti.unica.it>      |

<br>

---

<br>

> ### **Table of Content**
>  1. [Introduzione al problema](#introduzione-al-problema)
>  1. [Shortest (Longest) Path Problem](#shortest-longest-path-problem)
>  1. [Requisiti, utilizzo ed output](#requisiti-utilizzo-ed-output)


```
REPOSITORY STRUCTURE
·
│
│ FOLDERS
├── source          //codice sorgente
│   └── main.py
│
│ FILES
├── README.md
└── .gitignore
```

<br>
<br>

## **Introduzione al problema**
Il *Problema dello Zaino* (o *Knapsack Problem*, *KP*) è un problema di ottimizzazione combinatoria che consiste nel trovare il modo più efficiente di riempire uno zaino con oggetti di vario peso e valore. Il problema è di tipo NP-hard, ovvero non esiste un algoritmo polinomiale che lo risolva in tempo polinomiale, ma esistono algoritmi che lo risolvono in tempo pseudo-polinomiale.

Il problema è formulato come segue: dato uno zaino di capacità $W$ e una serie $N$ di oggetti, ognuno caratterizzato da un peso $w$ e un valore $v$, trovare il modo di riempire lo zaino in modo da massimizzare il valore totale degli oggetti inseriti, rispettando la capacità dello zaino.

La funzione obiettivo da massimizzare è la seguente:
$$ Z = \sum_{i=1}^{n} v_i \cdot x_i $$
$x_i$ è la variabile decisionale che indica se l'oggetto $i$ è stato inserito nello zaino o meno.

I vincoli da rispettare sono:
$$ \sum_{i=1}^{n} w_i \cdot x_i \leq W $$

In base al tipo di variabile decisionale $x_i$ si possono avere tre tipi di KP:
- **0-1 Knapsack Problem**: $x_i \in \{0, 1\}$
- **Bounded Knapsack Problem**: $x_i \in \{0, 1, ..., b_i\}$
- **Unbounded Knapsack Problem**: $x_i \in \mathbb{N}$

**Nel nostro caso abbiamo trattato il KP come un 0-1 KP.**

Il problema viene trattato con tre diversi approcci:
- **Branch & Bound**: viene utilizzato CPLEX per risolvere il problema con un algoritmo di B&B
- **Programmazione Dinamica**: viene utilizzato un algoritmo di PD per risolvere il problema
- **Shortest (Longest) Path Problem**: viene modellato il problema come un problema di cammino minimo (massimo) su un grafo pesato
> *I primi due metori vengono trattati nel corso di **Decision Science**, mentre il terzo viene trattato nell'esame di **Network Flow Optimization***

<br>
<br>

## **Shortest (Longest) Path Problem**
Il problema del cammino minimo consiste nel trovare il cammino di costo minimo tra due nodi di un grafo pesato. Il problema può essere *"ribaltato"* per trovare il cammino di costo massimo tra due nodi di un grafo pesato andando a cambiare il segno dei costi degli archi.

Il Knapsack Problem può essere modellato come un problema di cammino massimo su un grafo pesato.  
Il grafo è composto da $N \cdot (W+1) + 2$ nodi, dove $N$ è il numero di oggetti e $W$ è la capacità dello zaino, mentre i due nodi aggiuntivi corrispondono al nodo *source* e al nodo *target*.  
Per ogni oggetto $x$ ci sono $W+1$ nodi, uno per ogni possibile peso attualmente presente nello zaino, quindi definiamo il nodo $x_i$ come il nodo corrispondente all'oggetto $x$ ($0 \le x < N$) quando stiamo occupando $i$ all'interno dello zaino, $0 \le i \le W$.  
Ogni nodo $x_i$ (ed il nodo source $s_0$) è collegato:
- al nodo $(x+1)_i$ con un arco di peso $0$
- al nodo $(x+1)_{i+(w+1)}$ con un arco di peso $v_x$ se $i+w_x \leq W$, altrimenti non è collegato a nessun altro nodo

I nodi corrispondenti all'ultimo oggetto sono collegati al nodo target $t$ con un arco di peso $0$.

Se andiamo a cercare il cammino di costo massimo tra il nodo $s_0$ e il nodo $t$ otteniamo il valore massimo che possiamo ottenere riempiendo lo zaino.  
Gli oggetti selezionati sono quelli nel cammino che hanno un arco entrante con peso maggiore di zero.

> Esempio: prendiamo in considerazione il seguente KP
> | *$x$* | 0   | 1   | 2   | 3   |
> | --- | --- | --- | --- | --- |
> | *$v$* | 40  | 15  | 20  | 10  |
> | *$w$* | 4   | 2   | 3   | 1   |
> $W = 5$
>
> Il grafo costruito sarà il seguente:
> ![graph](./images/graph_example.png)
> Il cammino di costo massimo tra il nodo $s_0$ e il nodo $t$ è il seguente:  
> [$s_0$, $0_4$, $1_6$, $2_6$, $3_6$, $t$]
> 
> Gli oggetti selezionati sono quindi $x = [0, 1]$  
> Il valore totale è $Z = 40 + 15 = 55$

<br>
<br>

<details>
<summary>
<h2>Requisiti, utilizzo ed output</h2>
</summary>

Requisiti per l'utilizzo del progetto:
- Python 3.9+ - *quello con cui abbiamo eseguito il progetto, potrebbe funzionare anche con versioni precedenti*
- pip 21.0+ - *quello con cui abbiamo eseguito il progetto, potrebbe funzionare anche con versioni precedenti*
- ILOG CPLEX Optimization Studio 22.1.1 - [[download link](https://www.ibm.com/it-it/products/ilog-cplex-optimization-studio)]

> Note:
> in base alla versione di Python installata potrebbe essere necessario utilizzare `pip3` al posto di `pip` e `python3` al posto di `python`

Clonata la repository, consigliamo di creare una propria `venv` dentro la cartella source:
```bash
cd <path_to_this_repo>/source
python -m venv <virtual_environment_name>
source <virtual_enviroment_name>/bin/activate
```

Nel progetto è stato utilizzato `docplex` (interfaccia Python per CPLEX) per la risoluzione del problema tramite Branch & Bound, mentre `networkx` e `pyvis` sono stati utilizzati rispettivamente per la creazione e la visualizzazione dei grafi.

Per installare le dipendenze:
```bash
# DS: installazione di docplex
python <path_to_CPLEX>/python/setup.py install
# NFO: networkx e pyvis per la creazione e visualizzazione dei grafi
pip install networkx
pip install pyvis
```

Una volta installate le dipendenze si può eseguire il progetto
```bash
python main.py
```

Il progetto produrrà in output il log di un test con una lista di items generata casualmente e una capacità dello zaino cauale secondo il pattern:
```
List of items:
Itm[0]:  value 7        weight 1
...
Itm[n]:  value 5        weight 10
Capacity: 10

========================================

<Tipo di algoritmo per la soluzione>
Profit = 28, Residual capacity = 2
x[0] = 1
x[3] = 1
...
x[7] = 1
Time = 0.033518075942993164

========================================

...

```

Insime al log verrà prodotto un grafo che rappresenta la modellazione del problema come shortest (longest) path problem. Il grafo verrà salvato nella cartella `source` con il nome `graph.html` e sarà visualizzabile tramite il proprio browser.

Successivamente verrà effettuato un 5 test con numero di items crescente [10, 50, 100, 500, 1000] e capacità dello zaino fissa, e verrà prodotto un log del tipo:
```
Number of items: 10
FObj BB: 37, Time BB: 0.01954793930053711
FObj PD: 37, Time PD: 3.695487976074219e-05
FObj SP: 37, Time SP: 0.00022411346435546875
Same solution: True

...
```
</details>
