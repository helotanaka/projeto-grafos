import tracemalloc
import json
import time
from typing import List, Tuple, Dict, Any

# import graph + algorithms
from src.graphs import graph
from src.graphs.algorithms import (
    bfs_ordem_camadas_ciclos_dir,
    dfs_ordem_camadas_ciclos_dir,
    dijkstra_path,
    dijkstra_path_length,
    bellman_ford_path,
    bellman_ford_path_length,
    NoPath,
    NegativeCycle,
    NodeNotFound,
)

# loader do dataset
from tests.test_bfs_dfs import carregar_grafo_dataset


#  Utilitário: medir tempo + memória

def measure_time_and_memory(fn, *args, measure_memory=True, **kwargs):
    if measure_memory:
        tracemalloc.start()

    start = time.perf_counter()
    result = fn(*args, **kwargs)
    end = time.perf_counter()

    elapsed = end - start

    if measure_memory:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return result, elapsed, peak
    else:
        return result, elapsed, None


#  Métricas BFS

def run_bfs_metrics(G: graph.Graph, sources: List[str]) -> Dict[str, Any]:
    results = {}
    for s in sources:
        try:
            (resultado, tempo, memoria) = measure_time_and_memory(
                bfs_ordem_camadas_ciclos_dir, G, s
            )
            _, camadas, ciclos = resultado
            results[s] = {
                "time": tempo,
                "memory_peak_bytes": memoria,
                "layers": len(camadas),
                "total_nodes_visited": sum(len(c) for c in camadas),
                "cycles_found": len(ciclos),
            }
        except NodeNotFound:
            results[s] = {"error": f"source '{s}' not found"}
    return results


#  Métricas DFS

def run_dfs_metrics(G: graph.Graph, sources: List[str]) -> Dict[str, Any]:
    results = {}
    for s in sources:
        try:
            (resultado, tempo, memoria) = measure_time_and_memory(
                dfs_ordem_camadas_ciclos_dir, G, s
            )
            _, camadas, ciclos = resultado
            results[s] = {
                "time": tempo,
                "memory_peak_bytes": memoria,
                "layers": len(camadas),
                "total_nodes_visited": sum(len(c) for c in camadas),
                "cycles_found": len(ciclos),
            }
        except NodeNotFound:
            results[s] = {"error": f"source '{s}' not found"}
    return results


#  Métricas Dijkstra

def run_dijkstra_metrics(G: graph.Graph, pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
    results = {}
    for (source, target) in pairs:
        try:
            (path, tpath, mem_path) = measure_time_and_memory(
                dijkstra_path, G, source, target
            )
            (dist, tdist, mem_dist) = measure_time_and_memory(
                dijkstra_path_length, G, source, target
            )
            results[f"{source}->{target}"] = {
                "compute_path_time": tpath,
                "compute_path_memory": mem_path,
                "compute_distance_time": tdist,
                "compute_distance_memory": mem_dist,
                "distance": dist,
                "path_length": len(path),
            }
        except NodeNotFound as e:
            results[f"{source}->{target}"] = {"error": str(e)}
        except NoPath:
            results[f"{source}->{target}"] = {"error": "No path"}
    return results


#  Métricas Bellman-Ford

def run_bellman_ford_metrics(G: graph.Graph, pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
    results = {}
    for (source, target) in pairs:
        try:
            (path, tpath, mem_path) = measure_time_and_memory(
                bellman_ford_path, G, source, target
            )
            (dist, tdist, mem_dist) = measure_time_and_memory(
                bellman_ford_path_length, G, source, target
            )
            results[f"{source}->{target}"] = {
                "compute_path_time": tpath,
                "compute_path_memory": mem_path,
                "compute_distance_time": tdist,
                "compute_distance_memory": mem_dist,
                "distance": dist,
                "path_length": len(path),
            }
        except NegativeCycle as e:
            results[f"{source}->{target}"] = {
                "error": "Negative cycle detected",
                "cycle_path": e.path,
                "cost": e.cost,
            }
        except NoPath:
            results[f"{source}->{target}"] = {"error": "No path"}
        except NodeNotFound as e:
            results[f"{source}->{target}"] = {"error": str(e)}
    return results




def run_full_metrics(
    G: graph.Graph,
    bfs_sources: List[str],
    dfs_sources: List[str],
    dijkstra_pairs: List[Tuple[str, str]],
    bellman_pairs: List[Tuple[str, str]],
    output_path: str,
):

    report = {
        "dataset": {
            "num_nodes": G.ordem(),
            "num_edges": G.tamanho(),
            "is_directed": True,
        },
        "metrics": {
            "BFS": run_bfs_metrics(G, bfs_sources),
            "DFS": run_dfs_metrics(G, dfs_sources),
            "Dijkstra": run_dijkstra_metrics(G, dijkstra_pairs),
            "Bellman-Ford": run_bellman_ford_metrics(G, bellman_pairs),
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    return report

#  EXECUÇÃO AUTOMÁTICA — sem CLI

if __name__ == "__main__":

    OUTPUT_FILE = "out/parte2_report.json"

    print("Carregando grafo do dataset CSV...")
    G = carregar_grafo_dataset()
    print(f"Grafo carregado: {G.ordem()} nós, {G.tamanho()} arestas.\n")

    #  AMOSTRAGEM (3 fontes / 3 pares)
    all_nodes = list(G.nos())

    sample_sources = all_nodes[:3] if len(all_nodes) >= 3 else all_nodes
    sample_pairs = [(u, v) for u in sample_sources for v in sample_sources if u != v]

    print("Usando amostras:")
    print(" - Sources:", sample_sources)
    print(" - Pairs:", sample_pairs, "\n")

    print("Gerando métricas...")
    run_full_metrics(
        G,
        bfs_sources=sample_sources,
        dfs_sources=sample_sources,
        dijkstra_pairs=sample_pairs,
        bellman_pairs=sample_pairs,
        output_path=OUTPUT_FILE
    )

    print(f"Relatório gerado em {OUTPUT_FILE}")