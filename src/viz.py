import os
from collections import Counter, defaultdict
from typing import Dict, Iterable, Tuple, Optional
import pandas as pd
import matplotlib.pyplot as plt

try:
    from pyvis.network import Network
except Exception:
    Network = None

# Diretório de saída para os arquivos de visualização
OUT_DIR = os.path.join("out", "visualizacoesPt1")


def _garantir_pasta_saida() -> None:
    """Garante que a pasta de saída exista."""
    os.makedirs(OUT_DIR, exist_ok=True)


def _iterar_arestas(G) -> Iterable[Tuple[str, str, float]]:
    """Percorre as arestas do grafo (não direcionado) sem duplicar pares."""
    vistos = set()
    for u, vizinhos in getattr(G, "adj", {}).items():
        for v, peso in vizinhos.items():
            a, b = (u, v) if u <= v else (v, u)
            if (a, b) in vistos:
                continue
            vistos.add((a, b))
            yield a, b, float(peso)


def _calcular_graus(G) -> Dict[str, int]:
    """Retorna o grau (número de conexões) de cada vértice (bairro)."""
    graus = {u: 0 for u in getattr(G, "adj", {}).keys()}
    for u, v, _ in _iterar_arestas(G):
        graus[u] += 1
        graus[v] += 1
    return graus


def _criar_pyvis(G):
    """Cria e retorna uma instância da visualização com PyVis."""
    if Network is None:
        raise RuntimeError("A biblioteca pyvis não está instalada.")
    net = Network(height="750px", width="100%", directed=False, bgcolor="#ffffff", notebook=False)
    return net


def _salvar_html(net: "Network", caminho: str) -> None:
    """Salva o grafo em HTML de forma compatível com o Windows."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    try:
        net.write_html(caminho, notebook=False, open_browser=False)
    except Exception:
        from jinja2 import Template
        if getattr(net, "template", None) is None:
            net.template = Template(
                "<html><head><meta charset='utf-8'><title>Grafo</title></head><body>{{ body }}</body></html>"
            )
        net.write_html(caminho, notebook=False, open_browser=False)


# 1) Mapa de cores por grau -------------------------------------------------
def mapa_cores(G, arquivo_html: str = os.path.join(OUT_DIR, "mapa_cores.html")) -> str:
    """Gera um mapa colorido: quanto mais conexões o bairro tem, mais intensa é a cor."""
    _garantir_pasta_saida()
    graus = _calcular_graus(G)
    if not graus:
        raise ValueError("O grafo está vazio.")

    max_grau = max(graus.values()) or 1
    net = _criar_pyvis(G)

    for bairro, grau in graus.items():
        intensidade = int(255 * (grau / max_grau))
        cor = f"rgb({intensidade},0,{255 - intensidade})"
        net.add_node(bairro, label=bairro, title=f"Grau: {grau}", color=cor)

    for u, v, peso in _iterar_arestas(G):
        net.add_edge(u, v, title=f"Peso: {peso}")

    _salvar_html(net, arquivo_html)
    with open(arquivo_html.replace(".html", "_nota.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Visualização dos bairros coloridos conforme o número de conexões (grau). "
            "Quanto mais conexões, mais intensa a cor — revelando os principais hubs urbanos."
        )
    return arquivo_html


# 2) Histograma de graus ----------------------------------------------------
def histograma_graus(G, arquivo_png: str = os.path.join(OUT_DIR, "histograma_graus.png")) -> str:
    """Cria um histograma mostrando a distribuição do número de conexões (graus)."""
    _garantir_pasta_saida()
    graus = list(_calcular_graus(G).values())
    if not graus:
        raise ValueError("O grafo está vazio.")

    plt.figure(figsize=(8, 5))
    bins = min(15, max(5, int(len(graus) ** 0.5)))
    plt.hist(graus, bins=bins, edgecolor="black")
    plt.xlabel("Número de conexões (grau)")
    plt.ylabel("Quantidade de bairros")
    plt.title("Distribuição dos graus dos bairros do Recife")
    plt.tight_layout()
    plt.savefig(arquivo_png, dpi=160)
    plt.close()

    dist = Counter(graus)
    pd.DataFrame({
        "grau": list(dist.keys()),
        "frequencia": list(dist.values())
    }).sort_values("grau").to_csv(
        os.path.join(OUT_DIR, "histograma_graus_freq.csv"),
        index=False,
        encoding="utf-8"
    )

    with open(arquivo_png.replace(".png", "_nota.txt"), "w", encoding="utf-8") as f:
        f.write(
            "O histograma mostra a distribuição dos graus. "
            "Uma cauda longa indica poucos bairros com muitas conexões (superconectores)."
        )
    return arquivo_png


# 3) Subgrafo TOP-10 por grau ----------------------------------------------
def subgrafo_top10_grau(G, arquivo_html: str = os.path.join(OUT_DIR, "subgrafo_top10_grau.html")) -> str:
    """Exibe apenas os 10 bairros mais conectados do grafo."""
    _garantir_pasta_saida()
    graus = _calcular_graus(G)
    if not graus:
        raise ValueError("O grafo está vazio.")

    top = [n for n, _ in sorted(graus.items(), key=lambda x: x[1], reverse=True)[:10]]
    net = _criar_pyvis(G)

    for bairro in top:
        grau = graus[bairro]
        net.add_node(bairro, label=f"{bairro} (grau={grau})", size=20 + 3 * grau, color="#ff7f0e")

    for u, v, peso in _iterar_arestas(G):
        if u in top and v in top:
            net.add_edge(u, v, title=f"Peso: {peso}")

    net.force_atlas_2based()
    _salvar_html(net, arquivo_html)

    with open(arquivo_html.replace(".html", "_nota.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Subgrafo contendo os 10 bairros mais conectados. "
            "Representa o núcleo da conectividade urbana do Recife."
        )
    return arquivo_html


# 4) Ranking de densidade de ego por microrregião --------------------------
def ranking_densidade_microrregiao(
    G,
    bairro_para_micro: Optional[Dict[str, str]] = None,
    arquivo_png: str = os.path.join(OUT_DIR, "ranking_densidade_ego_microrregiao.png"),
) -> str:
    """Calcula a densidade média das redes locais (ego) agrupadas por microrregião."""
    _garantir_pasta_saida()

    if bairro_para_micro is None:
        csv_path = os.path.join("out", "bairros_unique.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join("data", "bairros_unique.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError("Arquivo bairros_unique.csv não encontrado.")
        df = pd.read_csv(csv_path)
        bairro_para_micro = {
            str(r["bairro"]).strip().lower(): str(r["microrregiao"])
            for _, r in df.iterrows()
        }

    vizinhos = defaultdict(set)
    for u, v, _ in _iterar_arestas(G):
        vizinhos[u].add(v)
        vizinhos[v].add(u)

    def densidade_ego(bairro: str) -> float:
        ego = {bairro} | vizinhos.get(bairro, set())
        V = len(ego)
        if V < 2:
            return 0.0
        E = 0
        ego = list(ego)
        pos = {n: i for i, n in enumerate(ego)}
        mat = [[0] * V for _ in range(V)]
        for a, b, _ in _iterar_arestas(G):
            if a in pos and b in pos and mat[pos[a]][pos[b]] == 0:
                mat[pos[a]][pos[b]] = mat[pos[b]][pos[a]] = 1
                E += 1
        return (2 * E) / (V * (V - 1))

    dens_por_bairro = {b: densidade_ego(b) for b in getattr(G, "adj", {}).keys()}

    grupos = defaultdict(list)
    for b, dens in dens_por_bairro.items():
        micro = bairro_para_micro.get(str(b).strip().lower(), "Desconhecida")
        grupos[micro].append(dens)

    df_out = pd.DataFrame({
        "microrregiao": list(grupos.keys()),
        "densidade_media_ego": [sum(v) / len(v) if v else 0.0 for v in grupos.values()],
    }).sort_values("densidade_media_ego", ascending=False)

    csv_out = os.path.join(OUT_DIR, "ranking_densidade_ego_microrregiao.csv")
    df_out.to_csv(csv_out, index=False, encoding="utf-8")

    plt.figure(figsize=(10, 5))
    plt.bar(df_out["microrregiao"], df_out["densidade_media_ego"])
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Densidade média das redes locais (ego)")
    plt.title("Ranking de densidade média por microrregião")
    plt.tight_layout()
    plt.savefig(arquivo_png, dpi=160)
    plt.close()

    with open(arquivo_png.replace(".png", "_nota.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Microrregiões com maiores densidades médias indicam bairros mais interconectados localmente."
        )
    return arquivo_png