# Trabalho-Pratico-01-Inteligência-Artificial

# Agente Inteligente em Labirinto Discreto 🤖🧩

Este projeto implementa um agente inteligente capaz de navegar e operar em um labirinto bidimensional sob diferentes níveis de conhecimento e restrições. O sistema explora três paradigmas fundamentais de resolução de problemas em Inteligência Artificial: Busca Clássica, Busca Local e Busca Online.

Este repositório contém a entrega do Trabalho Prático da disciplina de Inteligência Artificial.

## 🎯 Objetivos e Escopo

O agente é testado em três cenários progressivos de complexidade:
1. **Labirinto Conhecido (Busca Clássica):** O mapa completo é visível desde o início. O objetivo é encontrar o percurso ótimo de A até B.
2. **Múltiplos Objetivos (Busca Local - *Em Desenvolvimento*):** O agente deve coletar itens obrigatórios ($C_i$) minimizando o custo total da rota antes de chegar ao destino.
3. **Labirinto Desconhecido (Busca Online - *Em Desenvolvimento*):** O agente descobre o ambiente progressivamente utilizando seu campo de visão e atualizando um modelo interno do mundo.

## ⚙️ Arquitetura e Algoritmos Implementados

Atualmente, o motor de roteamento base (Navegador) suporta os seguintes algoritmos de busca cega e heurística:

* **Busca em Largura (BFS)**
* **Busca em Profundidade (DFS)**
* **Busca de Custo Uniforme (UCS)**
* **Busca Gulosa (Greedy Best-First Search)**
* **Weighted A***
* **IDA***
* **A* Clássico** *(Utilizando distância de Manhattan como heurística admissível)*

## 🚀 Como Executar

**Pré-requisitos:**
* Python 3.x
* Módulo `pandas` (para análise de dados futura, caso necessário)

1. Clone este repositório.
2. Execute o script principal via terminal:
   ```bash
   python main.py
