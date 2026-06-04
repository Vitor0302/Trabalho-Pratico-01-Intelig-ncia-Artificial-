from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Set
from collections import deque
import heapq
import itertools
import math
import pandas as pd

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

    @property
    def tamanho_caminho(self) -> Optional[int]:
        return len(self.acoes) if self.encontrado else None
    

class LabirintoBusca:
    def __init__(self, filename: str):
        with open(filename, encoding='utf-8') as f:
            contents = f.read()

        if contents.count('A') != 1:
            raise ValueError('O labirinto deve ter exatamente um ponto inicial A.')
        if contents.count('B') != 1:
            raise ValueError('O labirinto deve ter exatamente um objetivo B.')
        if contents.count('C') == 1:
            raise ValueError("O labirinto deve conter pelo menos 1 ponto de coleta C.")

        linhas = contents.splitlines()
        self.altura = len(linhas)
        self.largura = max(len(linha) for linha in linhas)
        self.paredes = []
        self.coletas = []

        for i in range(self.altura):
            row = []
            for j in range(self.largura):
                char = linhas[i][j] if j < len(linhas[i]) else ' '
                if char == 'A':
                    self.inicio = (i, j)
                    row.append(False)
                elif char == 'B':
                    self.objetivo = (i, j)
                    row.append(False)
                elif char == 'C':
                    self.coletas.append((i, j))
                    row.append(False)
                elif char == ' ':
                    row.append(False)
                else:
                    row.append(True)
            self.paredes.append(row)

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

    def h(self, estado: Estado) -> float:
        """Heurística de Manhattan para movimentos ortogonais com custo unitário."""
        return abs(estado[0] - self.objetivo[0]) + abs(estado[1] - self.objetivo[1])

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

    def busca_largura(self) -> ResultadoBusca:
        inicio = No(self.inicio)
        fronteira = deque([inicio])
        em_fronteira = {self.inicio}
        explorados: Set[Estado] = set()
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0

        while fronteira:
            no = fronteira.popleft()
            em_fronteira.remove(no.estado)
            nos_explorados += 1
            ordem_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca('Busca em Largura (BFS)', True, caminho, acoes, nos_explorados, nos_expandidos, ordem_explorados)

            explorados.add(no.estado)
            nos_expandidos += 1

            for acao, estado, custo in self.vizinhos(no.estado):
                if estado not in explorados and estado not in em_fronteira:
                    filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                    fronteira.append(filho)
                    em_fronteira.add(estado)

        return ResultadoBusca('Busca em Largura (BFS)', False, [], [], nos_explorados, nos_expandidos, ordem_explorados)

    def busca_profundidade(self) -> ResultadoBusca:
        inicio = No(self.inicio)
        fronteira = [inicio]
        em_fronteira = {self.inicio}
        explorados: Set[Estado] = set()
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0

        while fronteira:
            no = fronteira.pop()
            em_fronteira.remove(no.estado)
            nos_explorados += 1
            ordem_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca('Busca em Profundidade (DFS)', True, caminho, acoes, nos_explorados, nos_expandidos, ordem_explorados)

            explorados.add(no.estado)
            nos_expandidos += 1

            for acao, estado, custo in self.vizinhos(no.estado):
                if estado not in explorados and estado not in em_fronteira:
                    filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                    fronteira.append(filho)
                    em_fronteira.add(estado)

        return ResultadoBusca('Busca em Profundidade (DFS)', False, [], [], nos_explorados, nos_expandidos, ordem_explorados)

    def busca_prioridade(self, nome: str, funcao_prioridade) -> ResultadoBusca:
        contador = itertools.count()
        inicio = No(self.inicio, g=0.0)
        fronteira = []
        heapq.heappush(fronteira, (funcao_prioridade(inicio), next(contador), inicio))
        melhor_g: Dict[Estado, float] = {self.inicio: 0.0}
        fechados: Set[Estado] = set()
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0

        while fronteira:
            _, _, no = heapq.heappop(fronteira)

            if no.estado in fechados:
                continue

            nos_explorados += 1
            ordem_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(nome, True, caminho, acoes, nos_explorados, nos_expandidos, ordem_explorados)

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

        return ResultadoBusca(nome, False, [], [], nos_explorados, nos_expandidos, ordem_explorados)

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

    def busca_idastar(self) -> ResultadoBusca:
        ordem_explorados: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0
        limite = self.h(self.inicio)
        inicio = No(self.inicio, g=0.0)

        def dfs_limitado(no: No, limite_atual: float, caminho_atual: Set[Estado]):
            nonlocal nos_explorados, nos_expandidos, ordem_explorados

            nos_explorados += 1
            ordem_explorados.append(no.estado)
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
                return ResultadoBusca('IDA*', True, caminho, acoes, nos_explorados, nos_expandidos, ordem_explorados)

            if temp == math.inf:
                return ResultadoBusca('IDA*', False, [], [], nos_explorados, nos_expandidos, ordem_explorados)

            limite = temp

def imprimir_labirinto(lab: LabirintoBusca, resultado: Optional[ResultadoBusca] = None, mostrar_explorados: bool = True):
    caminho = set(resultado.caminho) if resultado and resultado.encontrado else set()
    explorados = set(resultado.estados_explorados) if resultado and mostrar_explorados else set()

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
            elif estado in caminho:
                print('*', end='')
            elif estado in explorados:
                print('.', end='')
            else:
                print(' ', end='')
        print()
    print()


def imprimir_metricas(resultado: ResultadoBusca):
    print(f'Algoritmo executado: {resultado.algoritmo}')
    print(f'Solução encontrada: {"sim" if resultado.encontrado else "não"}')
    print(f'Nós explorados: {resultado.nos_explorados}')
    print(f'Nós expandidos: {resultado.nos_expandidos}')
    print(f'Tamanho do caminho encontrado: {resultado.tamanho_caminho}')


#lab = LabirintoBusca(r'C:\Users\victo\Desktop\lab2.txt')
#lab = LabirintoBusca(r"C:\Users\maria\OneDrive\Área de Trabalho\ascii-art.txt")


def menu_principal():
    lab = None
    
    while lab is None:
        caminho_arquivo = input('Cole aqui o caminho do seu labirinto (OBS Sem aspas):').strip()

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

    print('Escolha o algoritmo de busca:')
    print('1 - Busca em Largura (BFS)')
    print('2 - Busca em Profundidade (DFS)')
    print('3 - Busca de Custo Uniforme (UCS)')
    print('4 - Greedy Best-First Search')
    print('5 - Weighted A*')
    print('6 - IDA*')
    print('7 - A* (Clássico)')

    opcao = input('Digite a opção desejada [1-7]: ').strip()

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
    else:
        print('\n[Erro] Opção inválida. Reinicie o programa.')
        return

    print('\nSolução encontrada no labirinto:')
    imprimir_labirinto(lab, resultado=resultado, mostrar_explorados=True)
    imprimir_metricas(resultado)


if __name__ == '__main__':
    menu_principal()