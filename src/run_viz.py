import csv
import os
from typing import Dict
from src.graphs.graph import Graph
from src.viz import (
    mapa_cores,
    subgrafo_top10_grau,
    histograma_graus,
    ranking_densidade_microrregiao,
)

DATA_DIR = "data"
OUT_DIR = os.path.join("out", "visualizacoesPt1")


def _achar_coluna(opcoes, nomes):
    nomes = [n.strip().lower() for n in nomes or []]
    for opc in opcoes:
        if opc in nomes:
            return opc
    return None


def carregar_grafo() -> Graph:
    """Carrega o grafo a partir do arquivo data/adjacencias_bairros.csv"""
    G = Graph()
    caminho = os.path.join(DATA_DIR, "adjacencias_bairros.csv")
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with open(caminho, encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        if not leitor.fieldnames:
            raise ValueError("O CSV de adjacências está vazio ou sem cabeçalho.")

        col_origem = _achar_coluna(["bairro_origem", "origem", "source"], leitor.fieldnames)
        col_destino = _achar_coluna(["bairro_destino", "destino", "target"], leitor.fieldnames)
        col_peso = _achar_coluna(["peso", "weight"], leitor.fieldnames)

        if not col_origem or not col_destino:
            raise ValueError("Colunas de origem/destino não encontradas.")

        for linha in leitor:
            u = (linha.get(col_origem) or "").strip().lower()
            v = (linha.get(col_destino) or "").strip().lower()
            if not u or not v:
                continue
            peso = 1.0
            if col_peso and linha.get(col_peso):
                try:
                    peso = float(linha[col_peso])
                except ValueError:
                    peso = 1.0
            G.adicionar_aresta(u, v, peso)
            G.adicionar_aresta(v, u, peso)
    return G


def carregar_mapa_bairro_micro() -> Dict[str, str]:
    """Lê o arquivo bairros_unique.csv e devolve o dicionário bairro → microrregião."""
    caminhos = [os.path.join("out", "bairros_unique.csv"), os.path.join("data", "bairros_unique.csv")]
    arquivo = next((p for p in caminhos if os.path.exists(p)), None)
    if not arquivo:
        print("Aviso: bairros_unique.csv não encontrado. Ranking por microrregião pode ficar incompleto.")
        return {}
    import pandas as pd
    df = pd.read_csv(arquivo)
    return {str(r["bairro"]).strip().lower(): str(r["microrregiao"]) for _, r in df.iterrows()}


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Carregando grafo de bairros...")
    G = carregar_grafo()
    mapa_micro = carregar_mapa_bairro_micro()

    print("Gerando mapa de cores por grau...")
    mapa_cores(G, os.path.join(OUT_DIR, "mapa_cores.html"))

    print("Gerando subgrafo dos 10 bairros mais conectados...")
    subgrafo_top10_grau(G, os.path.join(OUT_DIR, "subgrafo_top10_grau.html"))

    print("Gerando histograma de graus...")
    histograma_graus(G, os.path.join(OUT_DIR, "histograma_graus.png"))

    print("Gerando ranking de densidade média das redes locais (ego) por microrregião...")
    ranking_densidade_microrregiao(G, mapa_micro, os.path.join(OUT_DIR, "ranking_densidade_ego_microrregiao.png"))

    print("\nTodas as visualizações foram salvas em:", OUT_DIR)