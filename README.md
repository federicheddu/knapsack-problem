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
>  1. [Utilizzo](#utilizzo)
> 


```
REPOSITORY STRUCTURE
·
│
│ FOLDERS
├── DS_source       //codice sorgente Decision Science
│   └── main.py
│
│ FILES
├── README.md
└── ...
```

<br>

---

<br>

## **Utilizzo**
Per entrambi i progetti è stato utilizzato python in versione 3.9.
Per quanto riguarda l'esecuzione del codice consigliamo consigliamo di creare una propria `venv` come *enviroment*.

### **Decision Science**
Nel progetto è stata impiegata l'interfaccia python di CPLEX `docplex`.

Dopo aver installato CPLEX sulla propria macchina [[download link](https://www.ibm.com/it-it/products/ilog-cplex-optimization-studio)], aprire l'enviroment su cui si vuole eseguire il codice e mandare il seguente comando per installare `docplex`:
```bash
python /home_of_applications/CPLEX_Studio_Community2211/python/setup.py install
```  
> **Note**
> Il path dove si trova il file setup.py può variare in base alla versione di CPLEX installata e la posizione dove CPLEX è stato installato.

L'enviroment è pronto per eseguire il file [main.py](DS_source/main.py) con i vari test.