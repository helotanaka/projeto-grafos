import csv
from pathlib import Path

from src.graphs.graph import Graph
from src.graphs.algorithms import (
    bfs_ordem_camadas_ciclos_dir,
    dfs_ordem_camadas_ciclos_dir,
)


def carregar_grafo_dataset():
    """
    Carregando o dataset completo
    """
    base = Path(__file__).resolve().parent.parent
    dataset_dir = base / "data" / "dataset_parte2"

    G = Graph(direcionado=True)

    caminho_csv = dataset_dir / "LRH2016_00_Base_Completa.csv"
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {caminho_csv}")

    with open(caminho_csv, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for linha in reader:
            origem = linha["nomemun_a"]
            destino = linha["nomemun_b"]
            tempo_str = linha["tempo"]

            try:
                peso = float(tempo_str)
            except Exception:
                continue

            G.adicionar_aresta(origem, destino, peso)

    return G


def validar_resultado(nome_alg, fonte, ordem, camadas, ciclos):
    """
    Regras gerais de validação 
    """
    print(f"\n{nome_alg} para fonte '{fonte}'")
    print(f"Visitados: {len(ordem)} nós | Camadas: {len(camadas)} | Ciclos: {len(ciclos)}")

    # Ordem deve ser não vazia
    assert len(ordem) > 0, f"{nome_alg}: ordem vazia para fonte {fonte}"

    # Camadas coerentes
    for camada in camadas:
        assert isinstance(camada, list), "Camada deve ser lista"
        assert len(camada) > 0, f"Camada vazia encontrada para fonte {fonte}"

    # Ciclos com tamanho mínimo coerente
    for ciclo in ciclos:
        assert len(ciclo) >= 2, f"Ciclo inválido (<2 nós): {ciclo}"

    print(f"{nome_alg} OK para {fonte}")


def testar_bfs(G):
    print(" testando BFS para todas as fontes do dataset:")


    for fonte in sorted(G.nos()):
        ordem, camadas, ciclos = bfs_ordem_camadas_ciclos_dir(G, fonte)
        validar_resultado("BFS", fonte, ordem, camadas, ciclos)


def testar_dfs(G):
    print(" testando DFS para todas as fontes do dataset:")


    for fonte in sorted(G.nos()):
        ordem, camadas, ciclos = dfs_ordem_camadas_ciclos_dir(G, fonte)
        validar_resultado("DFS", fonte, ordem, camadas, ciclos)


if __name__ == "__main__":
    print("Executando test_bfs_dfs.py")

    G = carregar_grafo_dataset()
    print(f"Grafo carregado com {G.ordem()} nós e {G.tamanho()} arestas.")

    testar_bfs(G)
    testar_dfs(G)

    print("\nTodos os testes referentes a BFS e DFS foram executados com sucesso.")