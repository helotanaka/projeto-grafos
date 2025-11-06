import csv, json, unicodedata, re
from pathlib import Path
from .graphs.graph import Graph
from .graphs.algorithms import dijkstra_path, dijkstra_path_length

ALIAS_BAIRROS = {
    "setubal": "boa viagem",
}

# Força a passagem por BV quando for de Nova Descoberta a Setúbal
MANDATORY_VIA = {
    ("nova descoberta", "setubal"): "boa viagem",
}

def _normalize(nome: str) -> str:
    if nome is None:
        return ""
    t = unicodedata.normalize("NFKD", str(nome))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("ç", "c")
    return t.strip().lower()

def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower())
    return s.strip("_")

def calcular_distancias():
    base = Path(__file__).resolve().parent.parent   # Raiz do projeto
    data_dir = base / "data"
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)

    # Monta o grafo a partir de adjacencias_bairros.csv
    G = Graph()
    with open(data_dir / "adjacencias_bairros.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u = _normalize(r["bairro_origem"])
            v = _normalize(r["bairro_destino"])
            w = float(r["peso"])
            G.adicionar_aresta(u, v, w)

    # Lê os pares de endereços de enderecos.csv e calcula distâncias
    resultados = []
    with open(data_dir / "enderecos.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            end_x = r["endereco_X"]
            end_y = r["endereco_Y"]
            bx_raw = r["bairro_X"]
            by_raw = r["bairro_Y"]

            bx_norm = _normalize(bx_raw)
            by_norm = _normalize(by_raw)

            # aplica alias para o caminho de setubal -> BV
            bx_obg = ALIAS_BAIRROS.get(bx_norm, bx_norm)
            by_obg = ALIAS_BAIRROS.get(by_norm, by_norm)

            # nó obrigatório
            via_node = MANDATORY_VIA.get((bx_norm, by_norm))

            # valida existência no grafo
            if not G.tem_no(bx_obg):
                raise KeyError(f"Bairro_X '{bx_raw}' não existe no grafo (normalizado: '{bx_obg}').")
            if not G.tem_no(by_obg):
                raise KeyError(f"Bairro_Y '{by_raw}' não existe no grafo (normalizado: '{by_obg}').")
            if via_node is not None and not G.tem_no(via_node):
                raise KeyError(f"Nó obrigatório '{via_node}' não existe no grafo.")

            # Dijkstra com ou sem o nó obrigatório
            if via_node is None:
                custo = dijkstra_path_length(G, bx_obg, by_obg)
                caminho = dijkstra_path(G, bx_obg, by_obg)
            else:
                custo1 = dijkstra_path_length(G, bx_obg, via_node)
                cam1 = dijkstra_path(G, bx_obg, via_node)

                custo2 = dijkstra_path_length(G, via_node, by_obg)
                cam2 = dijkstra_path(G, via_node, by_obg)

                caminho = cam1 + cam2[1:]  # evita duplicar o via_node
                custo = float(custo1) + float(custo2)

            resultados.append([end_x, end_y, bx_raw, by_raw, custo, " -> ".join(caminho)])

            # JSON para cada par ordenado
            json_name = f"percurso_{_slug(bx_raw)}_{_slug(by_raw)}.json"
            with open(out_dir / json_name, "w", encoding="utf-8") as jf:
                json.dump(
                    {"origem": bx_raw, "destino": by_raw, "custo": custo, "caminho": caminho},
                    jf, ensure_ascii=False, indent=2
                )

            # JSON exigido para Nova Descoberta -> Setúbal
            if (bx_norm, by_norm) == ("nova descoberta", "setubal"):
                with open(out_dir / "percurso_nova_descoberta_setubal.json", "w", encoding="utf-8") as jf:
                    json.dump(
                        {
                            "origem": bx_raw,
                            "destino": by_raw,
                            "no_obrigatorio": "Boa Viagem (Setúbal)",
                            "custo": custo,
                            "caminho": caminho,
                        },
                        jf, ensure_ascii=False, indent=2
                    )

    # Salva o CSV final
    with open(out_dir / "distancias_enderecos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["X", "Y", "bairro_X", "bairro_Y", "custo", "caminho"])
        w.writerows(resultados)
