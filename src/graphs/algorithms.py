from heapq import heappush, heappop
from typing import Callable, Dict, List, Tuple, Set, Optional
from collections import deque
from .graph import Graph

class NodeNotFound(KeyError):
    ...
class NetworkXNoPath(Exception):
    ...
class NetworkXNegativeCycle(Exception):
    def __init__(self, message: str, path: Optional[List[str]] = None, cost: Optional[float] = None):
        super().__init__(message)
        self.path = path
        self.cost = cost
    ...

def _weight_function(weight: str | Callable):
    if callable(weight):
        return weight
    def w(u, v, data):
        return data.get(weight, 1)
    return w

def _edge_as_data(weight: float):
    return {"weight": weight}

def _dijkstra_multisource(G: Graph, sources, weight_fn, target=None):
    dist: Dict[str, float] = {}
    seen: Dict[str, float] = {}
    pred: Dict[str, List[str]] = {}
    fringe: List[Tuple[float, str]] = []

    for s in sources:
        seen[s] = 0.0
        heappush(fringe, (0.0, s))
        pred[s] = []

    while fringe:
        d, v = heappop(fringe)
        if v in dist:
            continue
        dist[v] = d
        if v == target:
            break

        for u, w in G.vizinhos(v):
            cost = weight_fn(v, u, _edge_as_data(w))
            if cost is None:
                continue
            vu_dist = d + cost
            if u not in dist and (u not in seen or vu_dist < seen[u]):
                seen[u] = vu_dist
                heappush(fringe, (vu_dist, u))
                pred[u] = [v]
            elif vu_dist == seen.get(u):
                pred[u].append(v)
    return dist, pred

def dijkstra_path(G: Graph, source: str, target: str, weight: str | Callable = "weight") -> List[str]:
    if source not in G.nos():
        raise NodeNotFound(source)
    if target not in G.nos():
        raise NodeNotFound(target)
    weight_fn = _weight_function(weight)
    dist, pred = _dijkstra_multisource(G, [source], weight_fn, target)
    if target not in dist:
        raise NetworkXNoPath(f"No path from {source} to {target}")
    path = [target]
    while pred[path[-1]]:
        path.append(pred[path[-1]][0])
    path.reverse()
    return path

def dijkstra_path_length(G: Graph, source: str, target: str, weight: str | Callable = "weight") -> float:
    if source not in G.nos():
        raise NodeNotFound(source)
    if target not in G.nos():
        raise NodeNotFound(target)
    dist, _ = _dijkstra_multisource(G, [source], _weight_function(weight), target)
    if target not in dist:
        raise NetworkXNoPath(f"No path from {source} to {target}")
    return dist[target]

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

                        raise NetworkXNegativeCycle(
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

        raise NetworkXNegativeCycle(
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
        raise NetworkXNoPath(f"Não há caminho de {source} para {target}")

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
        raise NetworkXNoPath(f"Não há caminho de {source} para {target}")

    return dist[target]

def bfs_ordem_camadas_ciclos(
    G: Graph,
    source: str,
    max_cycles: int = 10
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

        for u, _w in G.vizinhos(v):
            if u not in visited:
                # Aresta de árvore (v -> u)
                visited.add(u)
                parent[u] = v
                dist[u] = dist[v] + 1
                fila.append(u)
            elif parent[v] != u:
                if len(cycles) >= max_cycles:
                    continue  # atingiu o limite de ciclos armazenados
                pv = path_to_root(v)
                pu = path_to_root(u)
                set_pu = set(pu)

                # encontra o menor antecessor em comum
                lca = next((x for x in pv if x in set_pu), None)
                if lca is None:
                    continue

                iv = pv.index(lca)
                iu = pu.index(lca)

                # Caminho 
                path_v = pv[: iv + 1]
                path_u = pu[:iu]  # exclui o lca
                cycle = path_v + path_u[::-1]

                if len(cycle) < 3:
                    continue

                key = tuple(cycle)
                key_rev = tuple(reversed(cycle))
                if key not in seen_cycles and key_rev not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(cycle)

    # monta as camadas a partir da distância (níveis) calculada na BFS
    layers_dict: Dict[int, List[str]] = {}
    for node, d in dist.items():
        layers_dict.setdefault(d, []).append(node)

    camadas: List[List[str]] = [layers_dict[d] for d in sorted(layers_dict)]

    return ordem, camadas, cycles
