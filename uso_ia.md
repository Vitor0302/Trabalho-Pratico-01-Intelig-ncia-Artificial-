# Auditoria do Uso de IA Generativa

Este documento registra como o grupo utilizou ferramentas de Inteligência
Artificial generativa durante o desenvolvimento do trabalho, conforme exigido
pela Seção 10 do enunciado. O uso seguiu o princípio de **apoio**: a IA foi
empregada para discutir conceitos, esclarecer dúvidas e explicar erros de
código, enquanto a modelagem, a implementação dos algoritmos e a validação dos
resultados foram conduzidas e compreendidas pelo grupo.

---

## 1. Ferramentas utilizadas

- **Claude (Anthropic)**: apoio em explicações conceituais e revisão de código.
- **Assistente de IA (consulta pontual)**: esclarecimento de um erro específico
  na busca online (descrito na Seção 6).

---

## 2. Principais prompts utilizados

Exemplos representativos dos prompts feitos pelos integrantes do grupo:

**Conceituais — Busca Clássica:**

- "No A\*, quando há duas células livres igualmente boas, qual delas o agente
  escolhe primeiro?" (critério de desempate)
- "A heurística de Manhattan é admissível neste domínio? Justifique."
- "Qual a diferença prática entre UCS e BFS no nosso labirinto de custo
  uniforme?"
- "Em quais condições o DFS pode não encontrar solução mesmo ela existindo?"
- "O que diferencia a busca gulosa do A\* em termos de otimalidade?"

**Conceituais — Modelagem PEAS e Função de Desempenho:**

- "O que caracteriza um agente baseado em objetivos com modelo interno? O
  nosso agente se encaixa nessa categoria?"
- "Faz sentido incluir movimentos inválidos na função de desempenho se o agente
  nunca tenta um movimento inválido por design?"
- "Como normalizar o tempo de execução (que é em segundos, valores muito
  pequenos) para que ele contribua na mesma escala que o custo do caminho?"
- "Por que penalizar a fronteira máxima em vez do tamanho médio da fronteira?"

**Conceituais — Busca Local:**

- "Qual a diferença entre um mínimo local e um platô no contexto do
  Hill-Climbing?"
- "Como os sideways moves ajudam a sair de platôs sem entrar em ciclos
  infinitos?"
- "Por que o Simulated Annealing pode aceitar uma solução pior que a atual?
  Isso não atrapalha a convergência?"
- "A temperatura inicial do SA deve ser proporcional ao custo do problema?
  Por quê?"
- "Se α (taxa de resfriamento) for muito próximo de 1, o que acontece com o
  SA na prática?"
- "Por que usar swap de dois pontos em vez de inverter um segmento inteiro
  como operador de vizinhança?"
- "A busca clássica e a busca online coletam os pontos `C` ou ignoram?"

**Conceituais — Busca Online:**

- "Por que o labirinto aleatório gerado por backtracking (perfect maze) sempre
  dá razão online/offline igual a 1?"
- "O resultado `1.000` na razão é 1 ou 1000?" (notação decimal)
- "Tem uma célula livre acima do agente, mas ele foi para a direita. Por quê?"
- "Como o mapa interno do agente online evolui ao longo dos passos?"

**De código (depuração):**

- "Por que meu código da busca online está pulando passos?" (Seção 6)

---

## 3. Conceitos esclarecidos pela IA

Estas conversas ajudaram o grupo a entender melhor o próprio código e a teoria
por trás dele:

- **Critério de desempate do A\***: quando duas células têm o mesmo `f = g + h`,
  o desempate segue a ordem de geração dos vizinhos (cima, baixo, esquerda,
  direita). A IA reforçou que isso é apenas desempate: o agente primeiro
  minimiza `f`, e a ordem só decide entre opções igualmente boas.
- **Por que o agente "ignorou" uma célula livre**: numa observação em que havia
  espaço livre acima mas o agente foi para a direita, a IA explicou que ele não
  vai para o primeiro espaço livre, e sim para o de menor `f` (mais próximo do
  objetivo); a célula livre de cima tinha `f` maior.
- **Pontos de coleta na busca clássica e online**: ambas tratam o `C` como
  célula livre comum (não o coletam); apenas a busca local usa os pontos `C`.
- **Razão online/offline em labirintos perfeitos**: como uma árvore tem um único
  caminho entre A e B, o agente é forçado a segui-lo, resultando em razão 1;
  para obter razão maior que 1 é preciso um mapa com ciclos.

---

## 4. Trechos de código sugeridos por IA

A IA auxiliou na escrita de funções auxiliares (visualização e coleta de
métricas), sempre revisadas e ajustadas pelo grupo. Os algoritmos de busca
(BFS, DFS, UCS, Gulosa, A\*, Hill-Climbing, Simulated Annealing e Replanning A\*)
foram implementados pelo grupo.

- **Visualização da trajetória online passo a passo**: gravação de um *snapshot*
  por passo (posição do agente + cópia do mapa interno) e função de animação no
  terminal.
- **Exportação das métricas para CSV**: menu que permite escolher para qual
  busca gerar o `.csv` (clássica, local, online ou todas) e a opção de informar
  o raio de percepção na busca online.
- **Geração de mapas de teste**: rotina auxiliar que parte de um labirinto
  perfeito e remove algumas paredes internas para criar ciclos, usada para obter
  um mapa em que a razão online/offline fica maior que 1.

---

## 5. Sugestões rejeitadas

- **Geração automática de pontos de coleta no labirinto da busca online**:
  optou-se por **não** inserir pontos `C` no modo online, já que o agente online
  apenas percorre de A até B; a presença de `C` seria apenas confusa. O gerador
  passou a aceitar um parâmetro para controlar isso, com padrão sem coletas.

---

## 6. Erro de implementação explicado pela IA (busca online)

Durante a implementação da busca online, o agente estava "pulando" passos no
mapa. A consulta à IA esclareceu a causa:

> **Pergunta:** Por que meu código agora está pulando "passos"?
>
> **IA:** Está pulando devido a esta linha
> `proximo_passo = rota_planejada.caminho[1]`. Mude o índice `1` para `0`.

> **Pergunta:** Agora ele está fazendo passo a passo, mas por que isso
> influenciou?
>
> **IA:** Como a função `reconstruir` ignora a casa onde o agente já está, a
> lista `caminho` começa no **primeiro passo seguinte**. Por exemplo, indo de
> (1,1) até (1,4): índice `[0]` = (1,2), índice `[1]` = (1,3), índice `[2]` =
> (1,4). Ao usar `caminho[1]`, o agente ia direto para (1,3), pulando a casa
> (1,2), e por isso o rastro ficava "furado", dando saltos de dois blocos (e
> ignorando uma eventual parede na casa pulada). Ao usar `caminho[0]`, ele anda
> exatamente uma casa por iteração e replaneja no turno seguinte, corrigindo o
> movimento.

**Validação do grupo:** após a correção (`caminho[1]` → `caminho[0]`), o grupo
executou a busca online em vários mapas e confirmou, pela visualização passo a
passo, que o agente passou a se mover uma célula por vez, sem atravessar
paredes.

---

## 7. Como o grupo validou a solução

- **Execução e inspeção visual**: rodou o agente nos três modos e acompanhou a
  trajetória passo a passo no terminal para conferir o comportamento.
- **Reprodutibilidade das métricas**: como as buscas clássica e online são
  determinísticas para um dado mapa, o grupo reexecutou os experimentos e
  confirmou que os números se repetem.
- **Conferência de propriedades teóricas**: verificou que BFS, UCS e A\*
  retornam o mesmo custo ótimo, que o DFS retorna caminhos piores e que a razão
  online/offline vale 1 em labirintos sem ciclos e cresce em labirintos com
  ciclos, coerente com a teoria.

---

## 8. Modificações feitas pelo grupo

- Ajuste da busca online (`caminho[1]` → `caminho[0]`) e teste do movimento
  célula a célula.
- Escolha e validação dos mapas de teste de cada modo, incluindo um mapa com
  ciclos para obter razão online/offline maior que 1.
- Decisão de registrar, na curva de convergência do Simulated Annealing, o custo
  da iteração corrente.
- Configuração do gerador de labirintos para não inserir pontos `C` no modo
  online.
- Definição dos pesos da função de desempenho J e das justificativas da
  modelagem PEAS.
