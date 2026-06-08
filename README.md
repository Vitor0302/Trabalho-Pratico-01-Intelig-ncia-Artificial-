# Trabalho-Pratico-01-Inteligência-Artificial

# Agente Inteligente em Labirinto Discreto 🤖🧩

Este projeto implementa um agente inteligente capaz de navegar e operar em um labirinto bidimensional sob diferentes níveis de conhecimento e restrições. O sistema explora três paradigmas fundamentais de resolução de problemas em Inteligência Artificial: Busca Clássica, Busca Local e Busca Online.

Este repositório contém a entrega do Trabalho Prático da disciplina de Inteligência Artificial.

## 🎯 Objetivos e Escopo

O agente é testado em três cenários progressivos de complexidade:
1. **Labirinto Conhecido (Busca Clássica):** O mapa completo é visível desde o início. O objetivo é encontrar o percurso ótimo de A até B.
2. **Múltiplos Objetivos (Busca Local):** O agente deve coletar itens obrigatórios ($C_i$) minimizando o custo total da rota antes de chegar ao destino.
3. **Labirinto Desconhecido (Busca Online):** O agente descobre o ambiente progressivamente utilizando seu campo de visão e atualizando um modelo interno do mundo.

## ⚙️ Arquitetura e Algoritmos Implementados

**Busca Clássica** (mapa conhecido, A → B):

* **Busca em Largura (BFS)**
* **Busca em Profundidade (DFS)**
* **Busca de Custo Uniforme (UCS)**
* **Busca Gulosa (Greedy Best-First Search)**
* **Weighted A***
* **IDA***
* **A* Clássico** *(Utilizando distância de Manhattan como heurística admissível)*

**Busca Local** (otimização da ordem de coleta dos pontos $C_i$):

* **Hill-Climbing** *(com random-restart e movimentos laterais/sideways)*
* **Simulated Annealing**

**Busca Online** (mapa desconhecido):

* **Replanning com A*** *(percepção local de raio r, modelo interno do mapa e replanejamento a cada nova descoberta)*

## 📊 Visualização

O projeto gera visualizações do comportamento do agente no terminal e em gráficos:

* Mapa original, caminho encontrado e nós explorados (busca clássica);
* Curva de convergência *iteração × melhor custo* (busca local);
* **Trajetória online passo a passo**, em dois formatos:
  * **animação ao vivo no terminal** (o agente `@` avança revelando o mapa, `?` = desconhecido);
  * **exportação em GIF** via matplotlib, ideal para anexar ao relatório.

  O menu de visualização aparece automaticamente após qualquer busca online (opções 2 ou 10).

## 🚀 Como Executar

**Pré-requisitos:**
* Python 3.x
* `matplotlib` e `Pillow` — para os gráficos de convergência e a exportação do GIF da trajetória online.

Instalação das dependências (Ubuntu/Debian):
```bash
sudo apt install python3-matplotlib python3-pil
```

Ou, em qualquer sistema com `pip` (de preferência dentro de um ambiente virtual):
```bash
pip install matplotlib pillow
```

> As animações no terminal e os algoritmos de busca funcionam sem dependências externas; `matplotlib`/`Pillow` são necessários apenas para os gráficos e a exportação do GIF.

