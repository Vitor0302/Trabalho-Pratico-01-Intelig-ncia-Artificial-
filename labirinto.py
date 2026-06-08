from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Set
from collections import deque
import heapq
import itertools
import math
import time
import random
import csv
Estado = Tuple[int, int]


@dataclass
class No:
    estado: Estado
    pai: Optional['No'] = None
    acao: Optional[str] = None
    g: float = 0.0

@dataclass
class ResultadoBusca:
    algoritmo: str
    encontrado: bool
    caminho: List[Estado]
    acoes: List[str]
    nos_explorados: int
    nos_expandidos: int
    estados_explorados: List[Estado]
    custo_caminho: float = 0.0
    tempo_execucao: float = 0.0
    max_fronteira: int = 0
    celulas_livres: int = 1

    @property
    def tamanho_caminho(self) -> Optional[int]:
        return len(self.acoes) if self.encontrado else None

    def calcular_j(
        self,
        omega: float = 100.0,  # peso do bônus por encontrar a solução
        alpha: float = 1.0,    # peso do custo do caminho percorrido
        beta:  float = 0.05,   # peso do número de nós expandidos
        gamma: float = 1000.0, # peso do tempo de execução em segundos
        theta: float = 0.1,    # peso do pico da fronteira
        eta:   float = 20.0    # peso da taxa de cobertura
    ) -> float:
        sucesso = 1.0 if self.encontrado else 0.0
        taxa_cobertura = self.nos_explorados / max(self.celulas_livres, 1)
        return (
            + omega * sucesso
            - alpha * self.custo_caminho
            - beta  * self.nos_expandidos
            - gamma * self.tempo_execucao
            - theta * self.max_fronteira
            - eta   * taxa_cobertura
        )

@dataclass
class ResultadoBuscaLocal:
    algoritmo: str
    melhor_ordem: List[Estado]
    melhor_custo: float
    pior_custo: float
    custo_medio: float
    tempo_execucao: float
    total_iteracoes: int
    num_execucoes: int
    curva_convergencia: List[float]
    taxa_sucesso: float = 0.0

@dataclass
class ResultadoBuscaOnline:
    algoritmo: str
    encontrado: bool
    trajetoria: List[Estado]
    custo_real: float
    total_movimentos: int
    celulas_reveladas: int
    celulas_revisitadas: int
    num_replanejamentos: int
    tempo_execucao: float
    custo_otimo_offline: float
    mapa_final_interno: list  # List[List[Optional[bool]]]
    # Snapshots passo a passo: cada item é (posicao_do_agente, copia_do_mapa_interno).
    # A trajetória até o passo k é simplesmente trajetoria[:k+1].
    frames: List[Tuple[Estado, list]] = field(default_factory=list)

    @property
    def razao_online_offline(self) -> float:
        if math.isinf(self.custo_otimo_offline) or self.custo_otimo_offline == 0:
            return math.inf
        return self.custo_real / self.custo_otimo_offline


class LabirintoBusca:
    def __init__(self, filename: Optional[str] = None, mapa_str: Optional[str] = None):
        if filename:
            with open(filename, encoding='utf-8') as f:
                contents = f.read()
        elif mapa_str:
            contents = mapa_str
        else:
            raise ValueError('Forneça um caminho de arquivo ou uma string de mapa.')

        if contents.count('A') != 1:
            raise ValueError('O labirinto deve ter exatamente um ponto inicial A.')
        if contents.count('B') != 1:
            raise ValueError('O labirinto deve ter exatamente um objetivo B.')

        linhas = contents.splitlines()
        self.altura = len(linhas)
        self.largura = max(len(linha) for linha in linhas)
        self.paredes = []
        self.coletas = []
        self.celulas_livres = 0

        for i in range(self.altura):
            row = []
            for j in range(self.largura):
                char = linhas[i][j] if j < len(linhas[i]) else ' '
                if char == 'A':
                    self.inicio = (i, j)
                    row.append(False)
                    self.celulas_livres += 1 
                elif char == 'B':
                    self.objetivo = (i, j)
                    row.append(False)
                    self.celulas_livres += 1
                elif char == 'C':
                    self.coletas.append((i, j))
                    row.append(False)
                    self.celulas_livres += 1
                elif char == ' ':
                    row.append(False)
                    self.celulas_livres += 1
                else:
                    row.append(True)
            self.paredes.append(row)

    @classmethod
    def gerar_aleatorio(cls, largura: int = 31, altura: int = 15, num_coletas: int = 0) -> 'LabirintoBusca':
        """Gera um labirinto aleatório via backtracking recursivo.

        num_coletas: quantidade de pontos de coleta C a inserir. O padrão é 0,
        pois o único uso atual é a busca online (opção 2), que vai apenas de A
        até B e não coleta os C. Use > 0 para gerar mapas com coletas."""
        if largura % 2 == 0: largura += 1
        if altura % 2 == 0: altura += 1

        grade = [['#' for _ in range(largura)] for _ in range(altura)]

        def carve(r: int, c: int):
            grade[r][c] = ' '
            direcoes = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            random.shuffle(direcoes)
            for dr, dc in direcoes:
                nr, nc = r + dr, c + dc
                if 1 <= nr < altura - 1 and 1 <= nc < largura - 1 and grade[nr][nc] == '#':
                    grade[r + dr // 2][c + dc // 2] = ' '
                    carve(nr, nc)

        carve(1, 1)
        grade[1][1] = 'A'
        grade[altura - 2][largura - 2] = 'B'

        espacos_vazios = [
            (r, c) for r in range(1, altura - 1) for c in range(1, largura - 1)
            if grade[r][c] == ' ' and (r, c) not in [(1, 1), (altura - 2, largura - 2)]
        ]
        for _ in range(num_coletas):
            if espacos_vazios:
                r, c = random.choice(espacos_vazios)
                grade[r][c] = 'C'
                espacos_vazios.remove((r, c))

        return cls(mapa_str='\n'.join(''.join(linha) for linha in grade))

    def vizinhos(self, estado: Estado):
        linha, coluna = estado
        candidatos = [
            ('up',    (linha - 1, coluna)),
            ('down',  (linha + 1, coluna)),
            ('left',  (linha, coluna - 1)),
            ('right', (linha, coluna + 1)),
        ]
        resultado = []
        for acao, (l, c) in candidatos:
            if 0 <= l < self.altura and 0 <= c < self.largura and not self.paredes[l][c]:
                resultado.append((acao, (l, c), 1.0))
        return resultado

    def h(self, estado: Estado, destino: Optional[Estado] = None) -> float:
        destino = destino or self.objetivo
        return abs(estado[0] - destino[0]) + abs(estado[1] - destino[1])

    @staticmethod
    def reconstruir(no: No):
        estados = []
        acoes = []
        atual = no
        while atual.pai is not None:
            estados.append(atual.estado)
            acoes.append(atual.acao)
            atual = atual.pai
        estados.reverse()
        acoes.reverse()
        return estados, acoes

    # ------------------- BUSCA CLÁSSICA -----------------------------------

    def busca_largura(self) -> ResultadoBusca:
        t_inicio = time.perf_counter()
        max_fronteira = 0

        inicio = No(self.inicio)
        fronteira = deque([inicio])
        em_fronteira = {self.inicio}
        explorados: Set[Estado] = set()
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0

        while fronteira:
            max_fronteira = max(max_fronteira, len(fronteira))

            no = fronteira.popleft()
            em_fronteira.remove(no.estado)
            nos_explorados += 1
            ordem_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(
                    'Busca em Largura (BFS)', True, caminho, acoes,
                    nos_explorados, nos_expandidos, ordem_explorados,
                    custo_caminho=no.g,
                    tempo_execucao=time.perf_counter() - t_inicio,
                    max_fronteira=max_fronteira,
                    celulas_livres=self.celulas_livres
                )

            explorados.add(no.estado)
            nos_expandidos += 1

            for acao, estado, custo in self.vizinhos(no.estado):
                if estado not in explorados and estado not in em_fronteira:
                    filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                    fronteira.append(filho)
                    em_fronteira.add(estado)

        return ResultadoBusca(
            'Busca em Largura (BFS)', False, [], [],
            nos_explorados, nos_expandidos, ordem_explorados,
            tempo_execucao=time.perf_counter() - t_inicio,
            max_fronteira=max_fronteira,
            celulas_livres=self.celulas_livres
        )

    def busca_profundidade(self) -> ResultadoBusca:
        t_inicio = time.perf_counter()
        max_fronteira = 0

        inicio = No(self.inicio)
        fronteira = [inicio]
        em_fronteira = {self.inicio}
        explorados: Set[Estado] = set()
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0

        while fronteira:
            max_fronteira = max(max_fronteira, len(fronteira))

            no = fronteira.pop()
            em_fronteira.remove(no.estado)
            nos_explorados += 1
            ordem_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(
                    'Busca em Profundidade (DFS)', True, caminho, acoes,
                    nos_explorados, nos_expandidos, ordem_explorados,
                    custo_caminho=no.g,
                    tempo_execucao=time.perf_counter() - t_inicio,
                    max_fronteira=max_fronteira,
                    celulas_livres=self.celulas_livres
                )

            explorados.add(no.estado)
            nos_expandidos += 1

            for acao, estado, custo in self.vizinhos(no.estado):
                if estado not in explorados and estado not in em_fronteira:
                    filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                    fronteira.append(filho)
                    em_fronteira.add(estado)

        return ResultadoBusca(
            'Busca em Profundidade (DFS)', False, [], [],
            nos_explorados, nos_expandidos, ordem_explorados,
            tempo_execucao=time.perf_counter() - t_inicio,
            max_fronteira=max_fronteira,
            celulas_livres=self.celulas_livres
        )

    def busca_prioridade(
        self, nome: str, funcao_prioridade, 
        origem: Optional[Estado] = None, destino: Optional[Estado] = None
    ) -> ResultadoBusca:
        t_inicio = time.perf_counter()
        max_fronteira = 0

        origem = origem or self.inicio
        destino = destino or self.objetivo

        contador = itertools.count()
        inicio = No(origem, g=0.0)
        fronteira = []
        heapq.heappush(fronteira, (funcao_prioridade(inicio), next(contador), inicio))
        melhor_g: Dict[Estado, float] = {origem: 0.0}
        fechados: Set[Estado] = set()
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0

        while fronteira:
            max_fronteira = max(max_fronteira, len(fronteira))

            _, _, no = heapq.heappop(fronteira)

            if no.estado in fechados:
                continue

            nos_explorados += 1
            ordem_explorados.append(no.estado)

            if no.estado == destino:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(
                    nome, True, caminho, acoes,
                    nos_explorados, nos_expandidos, ordem_explorados,
                    custo_caminho=no.g,
                    tempo_execucao=time.perf_counter() - t_inicio,
                    max_fronteira=max_fronteira,
                    celulas_livres=self.celulas_livres
                )

            fechados.add(no.estado)
            nos_expandidos += 1

            for acao, estado, custo in self.vizinhos(no.estado):
                novo_g = no.g + custo
                if estado in fechados:
                    continue
                if novo_g < melhor_g.get(estado, math.inf):
                    filho = No(estado=estado, pai=no, acao=acao, g=novo_g)
                    melhor_g[estado] = novo_g
                    heapq.heappush(fronteira, (funcao_prioridade(filho), next(contador), filho))

        return ResultadoBusca(
            nome, False, [], [],
            nos_explorados, nos_expandidos, ordem_explorados,
            tempo_execucao=time.perf_counter() - t_inicio,
            max_fronteira=max_fronteira,
            celulas_livres=self.celulas_livres
        )

    def busca_custo_uniforme(self) -> ResultadoBusca:
        return self.busca_prioridade(
            'Busca de Custo Uniforme (UCS)',
            lambda no: no.g
        )

    def busca_gulosa(self) -> ResultadoBusca:
        return self.busca_prioridade(
            'Greedy Best-First Search',
            lambda no: self.h(no.estado)
        )

    def busca_weighted_astar(self, peso: float = 2.0) -> ResultadoBusca:
        if peso <= 0:
            raise ValueError('O peso da Weighted A* deve ser positivo.')
        return self.busca_prioridade(
            f'Weighted A* (w={peso})',
            lambda no: no.g + peso * self.h(no.estado)
        )

    def busca_astar(self, origem: Optional[Estado] = None, destino: Optional[Estado] = None) -> ResultadoBusca:
        origem = origem or self.inicio
        destino = destino or self.objetivo
        return self.busca_prioridade(
            'A* (Clássico)',
            lambda no: no.g + self.h(no.estado, destino),
            origem=origem,
            destino=destino
        )

    def busca_idastar(self) -> ResultadoBusca:
        t_inicio = time.perf_counter()
        max_profundidade = 0

        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0
        limite = self.h(self.inicio)
        inicio = No(self.inicio, g=0.0)

        def dfs_limitado(no: No, limite_atual: float, caminho_atual: Set[Estado]):
            nonlocal nos_explorados, nos_expandidos, ordem_explorados, max_profundidade

            nos_explorados += 1
            ordem_explorados.append(no.estado)
            max_profundidade = max(max_profundidade, int(no.g))
            f = no.g + self.h(no.estado)

            if f > limite_atual:
                return f, None

            if no.estado == self.objetivo:
                return 'FOUND', no

            nos_expandidos += 1
            menor_proximo_limite = math.inf

            vizinhos_ordenados = sorted(
                self.vizinhos(no.estado),
                key=lambda item: no.g + item[2] + self.h(item[1])
            )

            for acao, estado, custo in vizinhos_ordenados:
                if estado in caminho_atual:
                    continue

                filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                caminho_atual.add(estado)
                temp, solucao = dfs_limitado(filho, limite_atual, caminho_atual)
                caminho_atual.remove(estado)

                if temp == 'FOUND':
                    return 'FOUND', solucao
                if temp < menor_proximo_limite:
                    menor_proximo_limite = temp

            return menor_proximo_limite, None

        while True:
            temp, solucao = dfs_limitado(inicio, limite, {self.inicio})

            if temp == 'FOUND':
                caminho, acoes = self.reconstruir(solucao)
                return ResultadoBusca(
                    'IDA*', True, caminho, acoes,
                    nos_explorados, nos_expandidos, ordem_explorados,
                    custo_caminho=solucao.g,
                    tempo_execucao=time.perf_counter() - t_inicio,
                    max_fronteira=max_profundidade,
                    celulas_livres=self.celulas_livres
                )

            if temp == math.inf:
                return ResultadoBusca(
                    'IDA*', False, [], [],
                    nos_explorados, nos_expandidos, ordem_explorados,
                    tempo_execucao=time.perf_counter() - t_inicio,
                    max_fronteira=max_profundidade,
                    celulas_livres=self.celulas_livres
                )

            limite = temp

    # ------------------- BUSCA LOCAL -----------------------------------

    def distancia_astar(self, origem: Estado, destino: Estado) -> float:
        h_local = lambda e: abs(e[0] - destino[0]) + abs(e[1] - destino[1])
        contador = itertools.count()
        fronteira = [(h_local(origem), next(contador), origem, 0.0)]
        melhor_g: Dict[Estado, float] = {origem: 0.0}
        fechados: Set[Estado] = set()
        while fronteira:
            _, _, estado, g = heapq.heappop(fronteira)
            if estado in fechados:
                continue
            if estado == destino:
                return g
            fechados.add(estado)
            for _, viz, custo in self.vizinhos(estado):
                novo_g = g + custo
                if viz not in fechados and novo_g < melhor_g.get(viz, math.inf):
                    melhor_g[viz] = novo_g
                    f = novo_g + h_local(viz)
                    heapq.heappush(fronteira, (f, next(contador), viz, novo_g))
        return math.inf

    def caminho_astar_segmento(self, origem: Estado, destino: Estado) -> List[Estado]:
        h_local = lambda e: abs(e[0] - destino[0]) + abs(e[1] - destino[1])
        contador = itertools.count()
        fronteira = [(h_local(origem), next(contador), origem, 0.0)]
        melhor_g: Dict[Estado, float] = {origem: 0.0}
        pais: Dict[Estado, Optional[Estado]] = {origem: None}
        fechados: Set[Estado] = set()

        while fronteira:
            _, _, estado, g = heapq.heappop(fronteira)
            if estado in fechados:
                continue
            if estado == destino:
                path, atual = [], destino
                while atual is not None:
                    path.append(atual)
                    atual = pais[atual]
                path.reverse()
                return path
            fechados.add(estado)
            for _, viz, custo in self.vizinhos(estado):
                novo_g = g + custo
                if viz not in fechados and novo_g < melhor_g.get(viz, math.inf):
                    melhor_g[viz] = novo_g
                    pais[viz] = estado
                    heapq.heappush(fronteira, (novo_g + h_local(viz), next(contador), viz, novo_g))
        return []

    def pre_computar_distancias(self) -> Dict[Tuple[Estado, Estado], float]:
        pontos = [self.inicio] + self.coletas + [self.objetivo]
        dist: Dict[Tuple[Estado, Estado], float] = {}
        for origem in pontos:
            for destino in pontos:
                if origem != destino:
                    dist[(origem, destino)] = self.distancia_astar(origem, destino)
        return dist

    def _custo_solucao(self, ordem: List[Estado], dist: Dict) -> float:
        seq = [self.inicio] + ordem + [self.objetivo]
        return sum(dist[(seq[i], seq[i + 1])] for i in range(len(seq) - 1))

    def _vizinhos_swap(self, ordem: List[Estado]) -> List[List[Estado]]:
        vizinhos = []
        n = len(ordem)
        for i in range(n):
            for j in range(i + 1, n):
                novo = ordem[:]
                novo[i], novo[j] = novo[j], novo[i]
                vizinhos.append(novo)
        return vizinhos

    def hill_climbing(
        self,
        num_reinicializacoes: int = 20,
        max_sideways: int = 10
    ) -> ResultadoBuscaLocal:
        
        if not self.coletas:
            raise ValueError('O labirinto não possui pontos de coleta C.')

        t_inicio = time.perf_counter()
        dist = self.pre_computar_distancias()

        melhor_global: List[Estado] = []
        melhor_custo_global = math.inf
        custos_finais: List[float] = []
        curva: List[float] = []
        total_iteracoes = 0

        for _ in range(num_reinicializacoes):
            atual = random.sample(self.coletas, len(self.coletas))
            custo_atual = self._custo_solucao(atual, dist)
            sideways_count = 0

            while True:
                vizinhos = self._vizinhos_swap(atual)
                if not vizinhos: 
                    break
                    
                melhor_viz = min(vizinhos, key=lambda v: self._custo_solucao(v, dist))
                custo_viz = self._custo_solucao(melhor_viz, dist)
                total_iteracoes += 1

                if custo_viz < custo_atual:
                    atual, custo_atual = melhor_viz, custo_viz
                    sideways_count = 0
                elif custo_viz == custo_atual and sideways_count < max_sideways:
                    atual, custo_atual = melhor_viz, custo_viz
                    sideways_count += 1
                else:
                    break

                if custo_atual < melhor_custo_global:
                    melhor_custo_global = custo_atual
                    melhor_global = atual[:]
                curva.append(melhor_custo_global)

            custos_finais.append(custo_atual)
            
            if custo_atual < melhor_custo_global:
                melhor_custo_global = custo_atual
                melhor_global = atual[:]
            curva.append(melhor_custo_global)

        taxa_sucesso = sum(1 for c in custos_finais if c == melhor_custo_global) / len(custos_finais)
        return ResultadoBuscaLocal(
            algoritmo='Hill-Climbing',
            melhor_ordem=melhor_global,
            melhor_custo=melhor_custo_global,
            pior_custo=max(custos_finais),
            custo_medio=sum(custos_finais) / len(custos_finais),
            tempo_execucao=time.perf_counter() - t_inicio,
            total_iteracoes=total_iteracoes,
            num_execucoes=num_reinicializacoes,
            curva_convergencia=curva,
            taxa_sucesso=taxa_sucesso
        )

    def simulated_annealing(
        self,
        num_execucoes: int = 5,
        T0_fator: float = 0.5,
        alpha: float = 0.995,
        T_min: float = 0.01,
        max_iter: int = 5000
    ) -> ResultadoBuscaLocal:

        if not self.coletas:
            raise ValueError('O labirinto não possui pontos de coleta C.')

        t_inicio = time.perf_counter()
        dist = self.pre_computar_distancias()

        melhor_global: List[Estado] = []
        melhor_custo_global = math.inf
        custos_finais: List[float] = []
        melhor_curva: List[float] = []
        total_iteracoes = 0

        for _ in range(num_execucoes):
            atual = random.sample(self.coletas, len(self.coletas))
            custo_atual = self._custo_solucao(atual, dist)

            T = max(T0_fator * custo_atual, 1.0)

            melhor_exec = atual[:]
            custo_melhor_exec = custo_atual
            curva_exec: List[float] = []
            t = 0

            while T > T_min and t < max_iter:
                i, j = random.sample(range(len(atual)), 2)
                vizinho = atual[:]
                vizinho[i], vizinho[j] = vizinho[j], vizinho[i]
                custo_viz = self._custo_solucao(vizinho, dist)

                delta = custo_viz - custo_atual
                if delta < 0 or random.random() < math.exp(-delta / T):
                    atual, custo_atual = vizinho, custo_viz

                if custo_atual < custo_melhor_exec:
                    custo_melhor_exec = custo_atual
                    melhor_exec = atual[:]

                curva_exec.append(custo_atual)

                T *= alpha
                t += 1
                total_iteracoes += 1

            custos_finais.append(custo_melhor_exec)
            if custo_melhor_exec < melhor_custo_global:
                melhor_custo_global = custo_melhor_exec
                melhor_global = melhor_exec[:]
                melhor_curva = curva_exec

        taxa_sucesso = sum(1 for c in custos_finais if c == melhor_custo_global) / len(custos_finais)
        return ResultadoBuscaLocal(
            algoritmo='Simulated Annealing',
            melhor_ordem=melhor_global,
            melhor_custo=melhor_custo_global,
            pior_custo=max(custos_finais),
            custo_medio=sum(custos_finais) / len(custos_finais),
            tempo_execucao=time.perf_counter() - t_inicio,
            total_iteracoes=total_iteracoes,
            num_execucoes=num_execucoes,
            curva_convergencia=melhor_curva,
            taxa_sucesso=taxa_sucesso
        )

    # ------------------- BUSCA ONLINE ----------------------------------

    def busca_online(
        self,
        raio_percepcao: int = 1,
        max_passos: int = 10000
    ) -> ResultadoBuscaOnline:
        t_inicio = time.perf_counter()

        # None = desconhecida, True = parede, False = livre
        mapa_interno: List[List] = [[None] * self.largura for _ in range(self.altura)]

        posicao = self.inicio
        mapa_interno[posicao[0]][posicao[1]] = False

        trajetoria: List[Estado] = [posicao]
        visitas: Dict[Estado, int] = {posicao: 1}
        celulas_reveladas: Set[Estado] = set()
        custo_real = 0.0
        num_replanejamentos = 0
        plano: List[Estado] = []
        frames: List[Tuple[Estado, list]] = []

        def snapshot():
            """Congela a posição atual e o que o agente já conhece do mapa."""
            frames.append((posicao, [row[:] for row in mapa_interno]))

        def perceber(pos: Estado) -> bool:
            """Revela células dentro do raio de percepção (vizinhança Manhattan)."""
            l, c = pos
            novidade = False
            candidatos = [(l, c)]
            for dist in range(1, raio_percepcao + 1):
                candidatos += [(l - dist, c), (l + dist, c), (l, c - dist), (l, c + dist)]
            for nl, nc in candidatos:
                if 0 <= nl < self.altura and 0 <= nc < self.largura:
                    if mapa_interno[nl][nc] is None:
                        mapa_interno[nl][nc] = self.paredes[nl][nc]
                        celulas_reveladas.add((nl, nc))
                        novidade = True
            return novidade

        def astar_interno(origem: Estado, destino: Estado) -> List[Estado]:
            """A* no mapa interno — células desconhecidas são tratadas como livres."""
            h = lambda e: abs(e[0] - destino[0]) + abs(e[1] - destino[1])
            cnt = itertools.count()
            heap = [(h(origem), next(cnt), origem, 0.0)]
            melhor_g: Dict[Estado, float] = {origem: 0.0}
            pais: Dict[Estado, Optional[Estado]] = {origem: None}
            fechados: Set[Estado] = set()
            while heap:
                _, _, estado, g = heapq.heappop(heap)
                if estado in fechados:
                    continue
                if estado == destino:
                    path, cur = [], destino
                    while cur is not None:
                        path.append(cur)
                        cur = pais[cur]
                    path.reverse()
                    return path
                fechados.add(estado)
                for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nl, nc = estado[0] + dl, estado[1] + dc
                    viz = (nl, nc)
                    if not (0 <= nl < self.altura and 0 <= nc < self.largura):
                        continue
                    if mapa_interno[nl][nc] is True:
                        continue
                    ng = g + 1.0
                    if viz not in fechados and ng < melhor_g.get(viz, math.inf):
                        melhor_g[viz] = ng
                        pais[viz] = estado
                        heapq.heappush(heap, (ng + h(viz), next(cnt), viz, ng))
            return []

        res_offline = self.busca_astar()
        custo_otimo = res_offline.custo_caminho if res_offline.encontrado else math.inf

        for _ in range(max_passos):
            nova_info = perceber(posicao)
            snapshot()  # registra o estado já com a percepção desta posição

            if posicao == self.objetivo:
                break

            prox_invalido = bool(plano) and mapa_interno[plano[0][0]][plano[0][1]] is True
            if nova_info or not plano or prox_invalido:
                novo_plano = astar_interno(posicao, self.objetivo)
                num_replanejamentos += 1
                plano = novo_plano[1:]
                if not plano:
                    break

            proximo = plano.pop(0)
            posicao = proximo
            custo_real += 1.0
            trajetoria.append(posicao)
            visitas[posicao] = visitas.get(posicao, 0) + 1

        encontrado = posicao == self.objetivo
        revisitadas = sum(1 for v in visitas.values() if v > 1)

        return ResultadoBuscaOnline(
            algoritmo=f'Busca Online — Replanning A* (r={raio_percepcao})',
            encontrado=encontrado,
            trajetoria=trajetoria,
            custo_real=custo_real,
            total_movimentos=len(trajetoria) - 1,
            celulas_reveladas=len(celulas_reveladas),
            celulas_revisitadas=revisitadas,
            num_replanejamentos=num_replanejamentos,
            tempo_execucao=time.perf_counter() - t_inicio,
            custo_otimo_offline=custo_otimo,
            mapa_final_interno=mapa_interno,
            frames=frames
        )


def imprimir_labirinto(
    lab: LabirintoBusca,
    resultado=None,
    mostrar_explorados: bool = True,
    caminho_local: Optional[List[Estado]] = None
):
    if caminho_local is not None:
        caminho = set(caminho_local)
        explorados: set = set()
    elif isinstance(resultado, ResultadoBuscaOnline):
        caminho = set(resultado.trajetoria) if resultado.encontrado else set()
        explorados = set()
    else:
        caminho = set(resultado.caminho) if resultado and resultado.encontrado else set()
        explorados = set(resultado.estados_explorados) if resultado and mostrar_explorados else set()

    coletas = set(lab.coletas)

    print()
    for i in range(lab.altura):
        for j in range(lab.largura):
            estado = (i, j)
            if lab.paredes[i][j]:
                print('#', end='')
            elif estado == lab.inicio:
                print('A', end='')
            elif estado == lab.objetivo:
                print('B', end='')
            elif estado in coletas:
                print('C', end='')
            elif estado in caminho:
                print('*', end='')
            elif estado in explorados:
                print('.', end='')
            else:
                print(' ', end='')
        print()
    print()


def imprimir_metricas(resultado: ResultadoBusca):
    taxa = resultado.nos_explorados / max(resultado.celulas_livres, 1)
    j = resultado.calcular_j()

    print(f'Algoritmo executado  : {resultado.algoritmo}')
    print(f'Solução encontrada   : {"sim" if resultado.encontrado else "não"}')
    print(f'Custo do caminho     : {resultado.custo_caminho:.1f}')
    print(f'Tamanho do caminho   : {resultado.tamanho_caminho}')
    print(f'Nós explorados       : {resultado.nos_explorados}')
    print(f'Nós expandidos       : {resultado.nos_expandidos}')
    print(f'Fronteira máxima     : {resultado.max_fronteira}')
    print(f'Taxa de cobertura    : {taxa:.1%}')
    print(f'Tempo de execução    : {resultado.tempo_execucao*1000:.3f} ms')
    print(f'\n  Escore J = {j:.2f}')


def plotar_curva_convergencia(curva: List[float], algoritmo: str):
    if len(curva) < 2:
        print('  (curva indisponível — menos de 2 pontos)')
        return
    try:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots(figsize=(10, 5))
        ax.plot(curva, color='steelblue', linewidth=1.5, label='Melhor custo')
        ax.set_xlabel('Iteração')
        ax.set_ylabel('Melhor custo encontrado')
        ax.set_title(f'Curva de Convergência — {algoritmo}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    except ImportError:
        print('  [Aviso] matplotlib não instalado. Execute: pip install matplotlib')


def imprimir_resultado_local(lab: LabirintoBusca, resultado: ResultadoBuscaLocal):
    nomes: Dict = {lab.inicio: 'A', lab.objetivo: 'B'}
    for idx, c in enumerate(lab.coletas):
        nomes[c] = f'C{idx + 1}'

    rota = ['A'] + [nomes.get(p, str(p)) for p in resultado.melhor_ordem] + ['B']

    print(f'\n{"=" * 54}')
    print(f'  {resultado.algoritmo}')
    print(f'{"=" * 54}')
    print(f'  Melhor rota    : {" → ".join(rota)}')
    print(f'  Melhor custo   : {resultado.melhor_custo:.1f}')
    print(f'  Pior custo     : {resultado.pior_custo:.1f}')
    print(f'  Custo médio    : {resultado.custo_medio:.1f}')
    print(f'  Tempo total    : {resultado.tempo_execucao * 1000:.2f} ms')
    print(f'  Iterações      : {resultado.total_iteracoes}')
    print(f'  Execuções      : {resultado.num_execucoes}')
    print(f'  Taxa de sucesso: {resultado.taxa_sucesso:.1%}')

    sequencia = [lab.inicio] + resultado.melhor_ordem + [lab.objetivo]
    caminho_completo: List[Estado] = []
    for i in range(len(sequencia) - 1):
        segmento = lab.caminho_astar_segmento(sequencia[i], sequencia[i + 1])
        caminho_completo.extend(segmento[:-1] if i < len(sequencia) - 2 else segmento)

    print('\nMelhor rota encontrada no labirinto:')
    imprimir_labirinto(lab, caminho_local=caminho_completo)
    plotar_curva_convergencia(resultado.curva_convergencia, resultado.algoritmo)



def imprimir_mapa_interno(lab: LabirintoBusca, resultado: ResultadoBuscaOnline):
    mapa = resultado.mapa_final_interno
    traj_set = set(resultado.trajetoria)
    coletas = set(lab.coletas)

    print()
    for i in range(lab.altura):
        for j in range(lab.largura):
            estado = (i, j)
            celula = mapa[i][j]
            if celula is None:
                print('?', end='')
            elif celula is True:
                print('#', end='')
            elif estado == lab.inicio:
                print('A', end='')
            elif estado == lab.objetivo:
                print('B', end='')
            elif estado in coletas:
                print('C', end='')
            elif estado in traj_set:
                print('*', end='')
            else:
                print(' ', end='')
        print()
    print()


def _render_frame_texto(
    lab: LabirintoBusca,
    pos: Estado,
    mapa: list,
    traj_set: Set[Estado]
) -> str:
    """Monta a string de um único frame da trajetória online.

    Legenda: @ agente | * trajetória | ? desconhecido | # parede | A B C."""
    coletas = set(lab.coletas)
    linhas = []
    for i in range(lab.altura):
        linha = []
        for j in range(lab.largura):
            estado = (i, j)
            celula = mapa[i][j]
            if estado == pos:
                linha.append('@')
            elif celula is None:
                linha.append('?')
            elif celula is True:
                linha.append('#')
            elif estado == lab.inicio:
                linha.append('A')
            elif estado == lab.objetivo:
                linha.append('B')
            elif estado in coletas:
                linha.append('C')
            elif estado in traj_set:
                linha.append('*')
            else:
                linha.append(' ')
        linhas.append(''.join(linha))
    return '\n'.join(linhas)


def animar_trajetoria_online(
    resultado: ResultadoBuscaOnline,
    lab: LabirintoBusca,
    delay: float = 0.15
):
    """Reproduz no terminal, passo a passo, o avanço do agente enquanto
    descobre o mapa. Cada frame mostra a posição atual (@), a trajetória já
    percorrida (*) e o que o agente ainda não viu (?)."""
    frames = resultado.frames
    if not frames:
        print('  (sem frames para animar)')
        return

    total = len(frames)
    trajetoria = resultado.trajetoria

    for k, (pos, mapa) in enumerate(frames):
        traj_set = set(trajetoria[:k + 1])
        # \033[H = cursor para o topo; \033[J = limpa daqui para baixo.
        print('\033[H\033[J', end='')
        print(f'  Trajetória online — passo {k + 1}/{total}'
              f'   (posição {pos})')
        print(_render_frame_texto(lab, pos, mapa, traj_set))
        print('\n  @ agente   * trajetória   ? desconhecido   # parede')
        time.sleep(delay)

    print(f'\n  Animação concluída — {total} passos, '
          f'{"objetivo alcançado" if resultado.encontrado else "objetivo NÃO alcançado"}.')


def exportar_animacao_online(
    resultado: ResultadoBuscaOnline,
    lab: LabirintoBusca,
    filename: str = 'trajetoria_online.gif',
    fps: int = 8
):
    frames = resultado.frames
    if not frames:
        print('  (sem frames para exportar)')
        return

    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
        from matplotlib.colors import ListedColormap
        import matplotlib.patches as mpatches
    except ImportError:
        print('  [Aviso] matplotlib não instalado. Execute: pip install matplotlib pillow')
        return

    # Códigos de categoria usados na grade numérica de cada frame.
    DESCONHECIDO, PAREDE, LIVRE, TRAJETO, COLETA, INICIO, OBJETIVO, AGENTE = range(8)
    cores = ['#1a1a1a', '#777777', '#ffffff', '#7fb3ff',
             '#ff9f1c', '#2ec27e', '#ffd60a', '#e63946']
    rotulos = ['Desconhecido', 'Parede', 'Livre', 'Trajetória',
               'Coleta (C)', 'Início (A)', 'Objetivo (B)', 'Agente']
    cmap = ListedColormap(cores)

    coletas = set(lab.coletas)
    trajetoria = resultado.trajetoria

    def grade_do_frame(k: int):
        pos, mapa = frames[k]
        traj_set = set(trajetoria[:k + 1])
        g = [[DESCONHECIDO] * lab.largura for _ in range(lab.altura)]
        for i in range(lab.altura):
            for j in range(lab.largura):
                estado = (i, j)
                celula = mapa[i][j]
                if estado == pos:
                    g[i][j] = AGENTE
                elif celula is None:
                    g[i][j] = DESCONHECIDO
                elif celula is True:
                    g[i][j] = PAREDE
                elif estado == lab.inicio:
                    g[i][j] = INICIO
                elif estado == lab.objetivo:
                    g[i][j] = OBJETIVO
                elif estado in coletas:
                    g[i][j] = COLETA
                elif estado in traj_set:
                    g[i][j] = TRAJETO
                else:
                    g[i][j] = LIVRE
        return g

    fig, ax = plt.subplots(figsize=(lab.largura / 2.2, lab.altura / 2.2))
    im = ax.imshow(grade_do_frame(0), cmap=cmap, vmin=0, vmax=7)
    titulo = ax.set_title('')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(
        handles=[mpatches.Patch(color=cores[i], label=rotulos[i]) for i in range(8)],
        loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8, frameon=False
    )
    fig.tight_layout()

    total = len(frames)

    def atualizar(k: int):
        im.set_data(grade_do_frame(k))
        titulo.set_text(f'Trajetória online — passo {k + 1}/{total}')
        return [im, titulo]

    anim = FuncAnimation(fig, atualizar, frames=total, interval=1000 / fps, blit=False)
    try:
        anim.save(filename, writer=PillowWriter(fps=fps))
        print(f'  [OK] Animação salva em: {filename}')
    except Exception as e:
        print(f'  [Erro] Não foi possível salvar o GIF ({e}). Instale Pillow: pip install pillow')
    finally:
        plt.close(fig)


def imprimir_metricas_online(resultado: ResultadoBuscaOnline):
    razao = resultado.razao_online_offline
    razao_str = f'{razao:.3f}' if not math.isinf(razao) else 'inf'

    print(f'\nAlgoritmo            : {resultado.algoritmo}')
    print(f'Solução encontrada   : {"sim" if resultado.encontrado else "não"}')
    print(f'Total de movimentos  : {resultado.total_movimentos}')
    print(f'Custo real percorrido: {resultado.custo_real:.1f}')
    print(f'Custo ótimo offline  : {resultado.custo_otimo_offline:.1f}')
    print(f'Razão online/offline : {razao_str}')
    print(f'Células reveladas    : {resultado.celulas_reveladas}')
    print(f'Células revisitadas  : {resultado.celulas_revisitadas}')
    print(f'Replanejamentos      : {resultado.num_replanejamentos}')
    print(f'Tempo de execução    : {resultado.tempo_execucao * 1000:.3f} ms')



def exportar_csv_busca_classica(
    lab: LabirintoBusca,
    filename: str = 'resultados_busca_classica.csv'
):
    """Roda todos os algoritmos de busca clássica no labirinto e grava as
    métricas obrigatórias (seção 5.3 do enunciado) em um arquivo .csv."""
    algoritmos = [
        lab.busca_largura,
        lab.busca_profundidade,
        lab.busca_custo_uniforme,
        lab.busca_gulosa,
        lab.busca_astar,
        lambda: lab.busca_weighted_astar(peso=2.0),
        lab.busca_idastar,
    ]
    colunas = [
        'Algoritmo', 'Sucesso', 'Custo', 'Tamanho_Caminho',
        'Nos_Explorados', 'Nos_Expandidos', 'Max_Fronteira', 'Tempo_ms'
    ]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        escritor = csv.writer(f)
        escritor.writerow(colunas)
        for executar in algoritmos:
            r = executar()
            escritor.writerow([
                r.algoritmo,
                'sim' if r.encontrado else 'nao',
                f'{r.custo_caminho:.1f}',
                r.tamanho_caminho if r.encontrado else '',
                r.nos_explorados,
                r.nos_expandidos,
                r.max_fronteira,
                f'{r.tempo_execucao * 1000:.3f}',
            ])
    print(f'  [OK] Métricas da busca clássica salvas em: {filename}')


def exportar_csv_busca_local(
    lab: LabirintoBusca,
    filename: str = 'resultados_busca_local.csv',
    num_reinicios: int = 20,
    num_execucoes_sa: int = 5
):
    """Roda Hill-Climbing e Simulated Annealing e grava as métricas
    obrigatórias da busca local (seção 6.5) em um arquivo .csv."""
    if not lab.coletas:
        print('  [Aviso] Labirinto sem pontos de coleta C — busca local não se aplica.')
        return
    resultados = [
        lab.hill_climbing(num_reinicializacoes=num_reinicios),
        lab.simulated_annealing(num_execucoes=num_execucoes_sa),
    ]
    colunas = [
        'Algoritmo', 'Melhor_Custo', 'Pior_Custo', 'Custo_Medio',
        'Total_Iteracoes', 'Num_Execucoes', 'Taxa_Sucesso', 'Tempo_ms'
    ]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        escritor = csv.writer(f)
        escritor.writerow(colunas)
        for r in resultados:
            escritor.writerow([
                r.algoritmo,
                f'{r.melhor_custo:.1f}',
                f'{r.pior_custo:.1f}',
                f'{r.custo_medio:.1f}',
                r.total_iteracoes,
                r.num_execucoes,
                f'{r.taxa_sucesso:.3f}',
                f'{r.tempo_execucao * 1000:.3f}',
            ])
    print(f'  [OK] Métricas da busca local salvas em: {filename}')


def exportar_csv_busca_online(
    lab: LabirintoBusca,
    filename: str = 'resultados_busca_online.csv',
    raio_percepcao: int = 1
):
    """Roda a busca online e grava as métricas obrigatórias (seção 7.4),
    incluindo a razão online/offline, em um arquivo .csv."""
    r = lab.busca_online(raio_percepcao=raio_percepcao)
    razao = r.razao_online_offline
    razao_str = f'{razao:.3f}' if not math.isinf(razao) else 'inf'
    colunas = [
        'Algoritmo', 'Sucesso', 'Total_Movimentos', 'Custo_Real',
        'Custo_Otimo_Offline', 'Razao_Online_Offline', 'Celulas_Reveladas',
        'Celulas_Revisitadas', 'Replanejamentos', 'Tempo_ms'
    ]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        escritor = csv.writer(f)
        escritor.writerow(colunas)
        escritor.writerow([
            r.algoritmo,
            'sim' if r.encontrado else 'nao',
            r.total_movimentos,
            f'{r.custo_real:.1f}',
            f'{r.custo_otimo_offline:.1f}',
            razao_str,
            r.celulas_reveladas,
            r.celulas_revisitadas,
            r.num_replanejamentos,
            f'{r.tempo_execucao * 1000:.3f}',
        ])
    print(f'  [OK] Métricas da busca online salvas em: {filename}')


def _menu_visualizacao_online(lab: LabirintoBusca, resultado: ResultadoBuscaOnline):
    """Oferece a visualização da trajetória online passo a passo:
    animação ao vivo no terminal e/ou exportação de GIF para o relatório."""
    if not resultado.frames:
        return

    print('\n─── Visualização da trajetória online (passo a passo) ───')
    print('1 - Assistir animação no terminal')
    print('2 - Exportar animação como GIF (matplotlib)')
    print('3 - Ambos')
    print('Enter - Pular')
    escolha = input('Escolha [1/2/3 ou Enter]: ').strip()

    if escolha in ('1', '3'):
        d = input('Atraso entre passos em segundos (padrão 0.15): ').strip()
        try:
            delay = float(d) if d else 0.15
        except ValueError:
            delay = 0.15
        animar_trajetoria_online(resultado, lab, delay=delay)

    if escolha in ('2', '3'):
        nome = input('Nome do arquivo (padrão trajetoria_online.gif): ').strip()
        exportar_animacao_online(resultado, lab, filename=nome or 'trajetoria_online.gif')


def menu_principal():
    print('================================================================')
    print('         Agente Inteligente em Labirinto        ')
    print('================================================================')
    print('Digite 1 caso queira colocar um caminho de labirinto via txt.')
    print('Digite 2 caso queira fazer uma Busca Online com um labirinto desconhecido.')

    escolha_origem = input('\nEscolha sua opção [1 ou 2]: ').strip()

    if escolha_origem == '2':
        print('\n[MÁQUINA] Construindo um labirinto aleatório e desconhecido para o agente...')
        lab = LabirintoBusca.gerar_aleatorio(largura=31, altura=15)

        print('\n[MÁQUINA] Print do Labirinto que foi criado (Apenas nós vemos as paredes):')
        imprimir_labirinto(lab, resultado=None, mostrar_explorados=False)

        print('\n[AGENTE] Iniciando exploração às cegas (Busca Online com Replanejamento)...')
        resultado_online = lab.busca_online()

        print('\n[AGENTE] Trajeto final percorrido até o objetivo:')
        imprimir_labirinto(lab, resultado=resultado_online, mostrar_explorados=False)
        print('Mapa interno final do agente (? = nunca visto):')
        imprimir_mapa_interno(lab, resultado_online)
        # A animação no terminal limpa a tela, então mostramos as métricas por último.
        _menu_visualizacao_online(lab, resultado_online)
        imprimir_metricas_online(resultado_online)
        return

    elif escolha_origem == '1':
        lab = None
        caminho_arquivo = None

        while lab is None:
            caminho_arquivo = input('\nCole aqui o caminho do seu labirinto (OBS Sem aspas): ').strip()
            try:
                lab = LabirintoBusca(caminho_arquivo)
                print('\n[Sucesso] Labirinto carregado!')
            except FileNotFoundError:
                print('\n[Erro] Arquivo não encontrado. Verifique o caminho e tente novamente.')
            except ValueError as e:
                print(f'\n[Erro de Validação do Mapa] {e}')
            except Exception as e:
                print(f'\n[Erro Inesperado] {e}')

        imprimir_labirinto(lab, resultado=None, mostrar_explorados=False)

        print('─── Busca Clássica ───────────────────')
        print('1 - Busca em Largura (BFS)')
        print('2 - Busca em Profundidade (DFS)')
        print('3 - Busca de Custo Uniforme (UCS)')
        print('4 - Greedy Best-First Search')
        print('5 - Weighted A*')
        print('6 - IDA*')
        print('7 - A* (Clássico)')
        print('─── Busca Local ─────────────────────')
        print('8 - Hill-Climbing (random-restart + sideways)')
        print('9 - Simulated Annealing')
        print('─── Busca Online ────────────────────')
        print('10 - Busca Online (Replanning com A*)')
        print('─── Experimentos ────────────────────')
        print('11 - Exportar todas as métricas para CSV')
        print('─────────────────────────────────────')

        opcao = input('Digite a opção desejada [1-11]: ').strip()

        if opcao in ('1', '2', '3', '4', '5', '6', '7'):
            if opcao == '1':
                resultado = lab.busca_largura()
            elif opcao == '2':
                resultado = lab.busca_profundidade()
            elif opcao == '3':
                resultado = lab.busca_custo_uniforme()
            elif opcao == '4':
                resultado = lab.busca_gulosa()
            elif opcao == '5':
                peso = float(input('Informe o peso w da Weighted A* (ex: 2.0): ').strip())
                resultado = lab.busca_weighted_astar(peso=peso)
            elif opcao == '6':
                resultado = lab.busca_idastar()
            elif opcao == '7':
                resultado = lab.busca_astar()

            print('\nSolução encontrada no labirinto:')
            imprimir_labirinto(lab, resultado=resultado, mostrar_explorados=True)
            imprimir_metricas(resultado)

        elif opcao == '8':
            if not lab.coletas:
                print('\n[Aviso] O labirinto não tem pontos C. Carregue um mapa com pontos de coleta.')
                return
            n = int(input('Número de reinícios (padrão 20): ').strip() or '20')
            s = int(input('Máximo de sideways consecutivos (padrão 10): ').strip() or '10')
            resultado_local = lab.hill_climbing(num_reinicializacoes=n, max_sideways=s)
            imprimir_resultado_local(lab, resultado_local)

        elif opcao == '9':
            if not lab.coletas:
                print('\n[Aviso] O labirinto não tem pontos C. Carregue um mapa com pontos de coleta.')
                return
            e = int(input('Número de execuções independentes (padrão 5): ').strip() or '5')
            a = float(input('Taxa de resfriamento alpha (padrão 0.995): ').strip() or '0.995')
            resultado_local = lab.simulated_annealing(num_execucoes=e, alpha=a)
            imprimir_resultado_local(lab, resultado_local)

        elif opcao == '10':
            r = int(input('Raio de percepção (padrão 1): ').strip() or '1')
            resultado_online = lab.busca_online(raio_percepcao=r)
            print('\nTrajeto percorrido pelo agente:')
            imprimir_labirinto(lab, resultado=resultado_online, mostrar_explorados=False)
            print('Mapa interno final do agente (? = nunca visto):')
            imprimir_mapa_interno(lab, resultado_online)
            # A animação no terminal limpa a tela, então mostramos as métricas por último.
            _menu_visualizacao_online(lab, resultado_online)
            imprimir_metricas_online(resultado_online)

        elif opcao == '11':
            print('\n[Experimentos] Rodando algoritmos e gerando arquivos .csv...')
            exportar_csv_busca_classica(lab)
            if lab.coletas:
                exportar_csv_busca_local(lab)
            else:
                print('  [Info] Sem pontos de coleta C — CSV de busca local não gerado.')
            exportar_csv_busca_online(lab)
            print('\n[OK] Arquivos .csv gerados na pasta atual.')

        else:
            print('\n[Erro] Opção inválida. Reinicie o programa.')

    else:
        print('\n[Erro] Opção de origem inválida. Encerrando.')


if __name__ == '__main__':
    menu_principal()
