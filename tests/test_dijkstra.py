import csv, json, unicodedata, re
from pathlib import Path
from time import time 
import tracemalloc
from src.graphs.graph import Graph
from src.graphs.algorithms import (
    dijkstra_path,
    dijkstra_path_length,
    NoPath,
)


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower())
    return s.strip("_")


def calcular_distancias():
    inicio_total = time()
    tracemalloc.start()

    base = Path(__file__).resolve().parent.parent
    data_dir = base / "data"
    dataset_dir = data_dir / "dataset_parte2"

    out_root = base / "out"
    out_root.mkdir(exist_ok=True)

    json_dir = out_root / "parte2"
    json_dir.mkdir(parents=True, exist_ok=True)

    G = Graph(direcionado=True)

    with open(dataset_dir / "LRH2016_00_Base_Completa.csv",
              newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for linha in reader:
            origem = linha["nomemun_a"]
            destino = linha["nomemun_b"]
            tempo_str = linha["tempo"]

            try:
                peso = float(tempo_str)
            except (TypeError, ValueError):
                continue

            if peso <= 0:
                continue

            G.adicionar_aresta(origem, destino, peso)
            G.adicionar_aresta(destino, origem, peso)

    resultados = []

    with open(dataset_dir / "enderecos_parte2.csv",
              newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for linha in reader:
            origem = linha["municipio_inicio"]
            destino = linha["municipio_destino"]

            if not G.tem_no(origem):
                raise KeyError(
                    f"Origem '{origem}' não existe no grafo (normalizado: '{origem}')."
                )
            if not G.tem_no(destino):
                raise KeyError(
                    f"Destino '{destino}' não existe no grafo (normalizado: '{destino}')."
                )

            try:
                custo = dijkstra_path_length(G, origem, destino)
                caminho = dijkstra_path(G, origem, destino)
            except NoPath:
                custo = None
                caminho = []

            resultados.append(
                [origem, destino, custo, " -> ".join(caminho)]
            )

            json_name = f"percurso_{_slug(origem)}_{_slug(destino)}.json"
            with open(json_dir / json_name, "w", encoding="utf-8") as jf:
                json.dump(
                    {
                        "origem": origem,
                        "destino": destino,
                        "custo": custo,
                        "caminho": caminho,
                    },
                    jf,
                    ensure_ascii=False,
                    indent=2,
                )

    csv_path = json_dir / "distancias_enderecos_parte2.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        w = csv.writer(file)
        w.writerow(["origem", "destino", "custo", "caminho"])
        w.writerows(resultados)

#report
    tempo_total = time() - inicio_total

    memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    report_path = json_dir / "parte2_report.json"
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except FileNotFoundError:
        report = {}

    report["dijkstra_parte2"] = {
        "tempo": tempo_total,
        "memoria": memoria_pico,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
