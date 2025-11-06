from heapq import heappush, heappop
from typing import Callable, Dict, List, Tuple
from .graph import Graph

# Exceções iguais às do NetworkX
class NodeNotFound(KeyError):
    ...                           # Ojeto especial Ellipsis = pass
class NetworkXNoPath(Exception):
    ...

# Função de peso compatível
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

# API pública compatível com NetworkX
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
