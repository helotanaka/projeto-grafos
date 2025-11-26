from heapq import heappush, heappop
from typing import Callable, Dict, List, Tuple, Set, Optional, Any
from collections import deque
from .graph import Graph


class NodeNotFound(KeyError):
# Quando um nó não existe no grafo
    def __init__(self, node: str):
        self.node = node
        super().__init__(f"Nó não encontrado no grafo: {node}")


class NoPath(Exception):
# Quando não existe caminho entre source e target.
    def __init__(
        self,
        message: str,
        source: str | None = None,
        target: str | None = None,
    ):
        super().__init__(message)
        self.source = source
        self.target = target


class NegativeCycle(Exception):
#Quando um ciclo negativo é detectado.
    def __init__(
        self,
        message: str,
        path: Optional[List[str]] = None,
        cost: Optional[float] = None,
    ):
        super().__init__(message)
        self.path = path
        self.cost = cost

def _weight_function(weight: str | Callable):
    if callable(weight):
        return weight
    def w(u, v, data):
        return data.get(weight, 1)
    return w

def _edge_as_data(weight: float):
    return {"weight": weight}


def dijkstra_path(grafo: Graph, origem: str, destino: str) -> List[str]:
    if not grafo.tem_no(origem):
        raise ValueError(f"Origem: '{origem}' não está no grafo.")
    if not grafo.tem_no(destino):
        raise ValueError(f"Destino: '{destino}' não está no grafo.")
    if grafo.possui_peso_negativo():
        raise ValueError("Peso negativo encontrado.")

    custo_minimo: Dict[str, float] = {origem: 0.0}
    no_predecessor: Dict[str, str] = {}
    fila_prioridade: List[Tuple[float, str]] = [(0.0, origem)]
    
    caminho_existe = False

    while fila_prioridade:
        custo_acumulado, no_atual = heappop(fila_prioridade)

        if no_atual == destino:
            caminho_existe = True
            break

        if custo_acumulado > custo_minimo.get(no_atual, float('inf')):
            continue

        for no_vizinho, peso_aresta in grafo.vizinhos(no_atual):
            novo_custo_total = custo_acumulado + peso_aresta
            
            if novo_custo_total < custo_minimo.get(no_vizinho, float('inf')):
                custo_minimo[no_vizinho] = novo_custo_total
                no_predecessor[no_vizinho] = no_atual
                heappush(fila_prioridade, (novo_custo_total, no_vizinho))

    if not caminho_existe:
        return []

    melhor_caminho = []
    passo_atual = destino
    
    while passo_atual != origem:
        melhor_caminho.append(passo_atual)
        passo_atual = no_predecessor[passo_atual]
        
    melhor_caminho.append(origem)
    
    return melhor_caminho[::-1]

def dijkstra_path_length(grafo: Graph, origem: str, destino: str) -> float:    
    if not grafo.tem_no(origem):
        raise ValueError(f"Origem: '{origem}' não está no grafo.")
    if not grafo.tem_no(destino):
        raise ValueError(f"Destino: '{destino}' não está no grafo.")
    if grafo.possui_peso_negativo():
        raise ValueError("Peso negativo encontrado.")

    custo_minimo: Dict[str, float] = {origem: 0.0}
    
    fila_prioridade: List[Tuple[float, str]] = [(0.0, origem)]
    
    while fila_prioridade:
        custo_acumulado, no_atual = heappop(fila_prioridade)

        if no_atual == destino:
            return custo_acumulado

        if custo_acumulado > custo_minimo.get(no_atual, float('inf')):
            continue

        for no_vizinho, peso_aresta in grafo.vizinhos(no_atual):
            novo_custo_total = custo_acumulado + peso_aresta
            
            if novo_custo_total < custo_minimo.get(no_vizinho, float('inf')):
                custo_minimo[no_vizinho] = novo_custo_total
                heappush(fila_prioridade, (novo_custo_total, no_vizinho))

    return float('inf')

def bellman_ford(
    G: Graph,
    source: str,
    target: str,
    weight: str | Callable = "weight",
):
    if source not in G.nos():
        raise NodeNotFound(source)

    weight_fn = _weight_function(weight)

    dist: Dict[str, float] = {source: 0.0}
    pred: Dict[str, str] = {source: None}
    in_queue: Set[str] = {source}
    queue = deque([source])
    count: Dict[str, int] = {source: 0}

    n = G.ordem()
    max_iterations = 2 * n
    iteration = 0

    target_reached = False
    target_stable_count = 0

    while queue and iteration < max_iterations:
        iteration += 1
        u = queue.popleft()
        in_queue.discard(u)

        u_dist = dist[u]

        improved = False
        for v, w in G.vizinhos(u):
            cost = weight_fn(u, v, _edge_as_data(w))
            if cost is None:
                continue

            nova_dist = u_dist + cost

            if v not in dist or nova_dist < dist[v]:
                dist[v] = nova_dist
                pred[v] = u
                improved = True

                if v == target:
                    target_reached = True
                    target_stable_count = 0

                if v not in in_queue:
                    queue.append(v)
                    in_queue.add(v)

                    count[v] = count.get(v, 0) + 1
                    if count[v] > n:
                        path = []
                        current = target if target in dist else v
                        visited = set()

                        while current is not None and current not in visited:
                            visited.add(current)
                            path.append(current)
                            current = pred.get(current)

                        path.reverse()

                        raise NegativeCycle(
                            f"Ciclo negativo detectado (nó '{v}' relaxado {count[v]} vezes)",
                            path=path if target in dist else [],
                            cost=dist.get(target),
                        )

        if target_reached and not improved:
            target_stable_count += 1
            if target_stable_count > n // 2:
                break

    if iteration >= max_iterations:
        path = []
        if target in dist:
            current = target
            visited = set()
            while current is not None and current not in visited:
                visited.add(current)
                path.append(current)
                current = pred.get(current)
            path.reverse()

        raise NegativeCycle(
            f"Limite de iterações atingido ({max_iterations}) - possível ciclo negativo",
            path=path,
            cost=dist.get(target),
        )

    return dist, pred

def bellman_ford_path(
    G: Graph,
    source: str,
    target: str,
    weight: str | Callable = "weight",
) -> List[str]:
    if source not in G.nos():
        raise NodeNotFound(source)
    if target not in G.nos():
        raise NodeNotFound(target)

    dist, pred = bellman_ford(G, source, target, weight)

    if target not in dist:
        raise NoPath(f"Não há caminho de {source} para {target}")

    path = []
    current = target
    visited = set()

    while current is not None:
        if current in visited:
            break
        visited.add(current)
        path.append(current)
        current = pred.get(current)

    path.reverse()
    return path


def bellman_ford_path_length(
    G: Graph,
    source: str,
    target: str,
    weight: str | Callable = "weight",
) -> float:
    if source not in G.nos():
        raise NodeNotFound(source)
    if target not in G.nos():
        raise NodeNotFound(target)

    dist, pred = bellman_ford(G, source, target, weight)

    if target not in dist:
        raise NoPath(f"Não há caminho de {source} para {target}")

    return dist[target]




def bfs_ordem_camadas_ciclos_dir(
    G: Graph,
    source: str,
    max_cycles: int = 10,
):
    if source not in G.nos():
        raise NodeNotFound(source)

    visited: Set[str] = {source}
    parent: Dict[str, Optional[str]] = {source: None}
    dist: Dict[str, int] = {source: 0}
    ordem: List[str] = []
    cycles: List[List[str]] = []
    seen_cycles: Set[Tuple[str, ...]] = set()

    fila = deque([source])

    def path_to_root(node: str) -> List[str]:
        path: List[str] = []
        while node is not None:
            path.append(node)
            node = parent.get(node)
        return path

    while fila:
        v = fila.popleft()
        ordem.append(v)

        # Grafo direcionado: segue arestas v -> u
        for u, _w in G.vizinhos(v):
            if u not in visited:
                # Aresta de árvore
                visited.add(u)
                parent[u] = v
                dist[u] = dist[v] + 1
                fila.append(u)

            # Aresta não-árvore: pode indicar ciclo direcionado
            elif parent[v] != u:
                if len(cycles) >= max_cycles:
                    # Atingiu limite de ciclos
                    continue

                pv = path_to_root(v)
                pu = path_to_root(u)
                set_pu = set(pu)

                # Encontra o menor ancestral comum
                lca = next((x for x in pv if x in set_pu), None)
                if lca is None:
                    continue

                iv = pv.index(lca)
                iu = pu.index(lca)

                path_v = pv[: iv + 1]  # de v até LCA
                path_u = pu[:iu]       # de u até antes do LCA
                cycle = path_v + path_u[::-1]

                # Ciclos de pelo menos 3 nós
                if len(cycle) < 3:
                    continue

                key = tuple(cycle)
                key_rev = tuple(reversed(cycle))
                if key not in seen_cycles and key_rev not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(cycle)

    # Monta camadas a partir das distâncias
    layers_dict: Dict[int, List[str]] = {}
    for node, d in dist.items():
        layers_dict.setdefault(d, []).append(node)

    camadas: List[List[str]] = [layers_dict[d] for d in sorted(layers_dict)]

    return ordem, camadas, cycles


def dfs_ordem_camadas_ciclos_dir(
    G: Graph,
    source: str,
    max_cycles: int = 10,
):
    if source not in G.nos():
        raise NodeNotFound(source)

    visited: Set[str] = set()
    parent: Dict[str, Optional[str]] = {source: None}
    depth: Dict[str, int] = {source: 0}
    ordem: List[str] = []
    cycles: List[List[str]] = []
    seen_cycles: Set[Tuple[str, ...]] = set()

    def path_to_root(node: str) -> List[str]:
        path: List[str] = []
        while node is not None:
            path.append(node)
            node = parent.get(node)
        return path

    # Pilha: (nó atual, iterador de vizinhos)
    stack: List[Tuple[str, Any]] = []

    visited.add(source)
    ordem.append(source)
    stack.append((source, iter(G.vizinhos(source))))

    while stack:
        v, neighbors_iter = stack[-1]
        try:
            u, _w = next(neighbors_iter)
        except StopIteration:
            # Terminou vizinhos de v, desempilha
            stack.pop()
            continue

        if u not in visited:
            # Aresta de árvore (v -> u)
            visited.add(u)
            parent[u] = v
            depth[u] = depth[v] + 1
            ordem.append(u)
            stack.append((u, iter(G.vizinhos(u))))
        elif parent[v] != u:
            # Aresta não-árvore: possível ciclo
            if len(cycles) >= max_cycles:
                return _montar_camadas_dfs(ordem, depth, cycles)

            pv = path_to_root(v)
            pu = path_to_root(u)
            set_pu = set(pu)

            # Encontra o menor ancestral comum
            lca = next((x for x in pv if x in set_pu), None)
            if lca is None:
                continue

            iv = pv.index(lca)
            iu = pu.index(lca)

            path_v = pv[: iv + 1]
            path_u = pu[:iu]  # Exclui lca
            cycle = path_v + path_u[::-1]

            if len(cycle) < 3:
                continue

            key = tuple(cycle)
            key_rev = tuple(reversed(cycle))
            if key not in seen_cycles and key_rev not in seen_cycles:
                seen_cycles.add(key)
                cycles.append(cycle)

    camadas = _montar_camadas_dfs(ordem, depth, cycles)[1]
    return ordem, camadas, cycles


def _montar_camadas_dfs(
    ordem: List[str],
    depth: Dict[str, int],
    cycles: List[List[str]],
):
    # Monta as camadas a partir da profundidade
    layers_dict: Dict[int, List[str]] = {}
    for node, d in depth.items():
        layers_dict.setdefault(d, []).append(node)
        
    camadas: List[List[str]] = [layers_dict[d] for d in sorted(layers_dict)]
    return ordem, camadas, cycles
