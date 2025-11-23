import csv, json, unicodedata, re
from pathlib import Path
from time import time

from src.graphs.graph import Graph
from src.graphs.algorithms import (
    bellman_ford_path,
    bellman_ford_path_length,
    NetworkXNoPath,
    NetworkXNegativeCycle,
    NodeNotFound,
)


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower())
    return s.strip("_")


def calcular_distancias_bellman_ford():
    inicio_total = time()

    base = Path(__file__).resolve().parent.parent
    data_dir = base / "data"
    dataset_dir = data_dir / "dataset_parte2"

    out_root = base / "out"
    out_root.mkdir(exist_ok=True)

    json_dir = out_root / "parte2"
    json_dir.mkdir(parents=True, exist_ok=True)

    G = Graph(direcionado=True)

    inicio = time()
    arestas_lidas = 0
    arestas_negativas = 0

    try:
        with open(
            dataset_dir / "LRH2016_00_Base_Completa.csv",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)

            for linha in reader:
                origem = linha["nomemun_a"]
                destino = linha["nomemun_b"]
                tempo_str = linha["tempo"]

                try:
                    peso = float(tempo_str)
                except (TypeError, ValueError):
                    continue

                G.adicionar_aresta(origem, destino, peso)
                arestas_lidas += 1

                if peso < 0:
                    arestas_negativas += 1

    except FileNotFoundError:
        print(f"ERRO: Arquivo de dados não encontrado em: {dataset_dir}")
        return

    tempo_construcao = time() - inicio

    resultados = []
    estatisticas = {
        "total": 0,
        "sucesso": 0,
        "sem_caminho": 0,
        "ciclo_negativo": 0,
        "erro_origem": 0,
        "erro_destino": 0,
        "outros_erros": 0,
    }

    tempos_calculo = []

    try:
        with open(
            dataset_dir / "enderecos_bellmanford.csv",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)
            rotas = list(reader)
            total_rotas = len(rotas)

            for idx, linha in enumerate(rotas, 1):
                origem = linha["municipio_inicio"]
                destino = linha["municipio_destino"]

                estatisticas["total"] += 1

                custo = None
                caminho = []

                if not G.tem_no(origem):
                    estatisticas["erro_origem"] += 1
                    print(f"[{idx}/{total_rotas}] Origem não existe: {origem}")

                elif not G.tem_no(destino):
                    estatisticas["erro_destino"] += 1
                    print(f"[{idx}/{total_rotas}] Destino não existe: {destino}")

                else:
                    inicio_rota = time()
                    timeout_segundos = 30

                    try:
                        custo = bellman_ford_path_length(G, origem, destino)

                        if time() - inicio_rota > timeout_segundos:
                            raise TimeoutError(f"Timeout de {timeout_segundos}s atingido")

                        caminho = bellman_ford_path(G, origem, destino)

                        tempo_rota = time() - inicio_rota
                        tempos_calculo.append(tempo_rota)

                        estatisticas["sucesso"] += 1

                    except NetworkXNegativeCycle as e:
                        custo = e.cost if hasattr(e, "cost") else None
                        caminho = e.path if hasattr(e, "path") else []

                        tempo_rota = time() - inicio_rota
                        tempos_calculo.append(tempo_rota)

                        estatisticas["ciclo_negativo"] += 1

                        print(f"[{idx}/{total_rotas}] CICLO NEGATIVO: {origem} → {destino}")
                        if caminho:
                            print(
                                "    Caminho encontrado (pode não ser mínimo): "
                                + " -> ".join(caminho[:5])
                                + "..."
                            )
                        if custo is not None:
                            print(f"    Custo (pode não ser mínimo): {custo:.2f}")

                    except NetworkXNoPath:
                        estatisticas["sem_caminho"] += 1
                        print(f"[{idx}/{total_rotas}] Sem caminho: {origem} → {destino}")

                    except NodeNotFound as e:
                        estatisticas["outros_erros"] += 1
                        print(f"[{idx}/{total_rotas}] Nó não encontrado: {e}")

                    except TimeoutError:
                        estatisticas["outros_erros"] += 1
                        print(f"[{idx}/{total_rotas}] TIMEOUT: {origem} → {destino}")
                        print(
                            "    Rota demorou mais de 30s - possível ciclo negativo complexo"
                        )

                    except Exception as e:
                        estatisticas["outros_erros"] += 1
                        print(f"[{idx}/{total_rotas}] Erro desconhecido: {e}")

                caminho_str = " -> ".join(caminho) if caminho else ""

                resultados.append([origem, destino, custo, caminho_str])

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

    except FileNotFoundError:
        print("ERRO: Arquivo de endereços não encontrado.")
        return

    csv_path = json_dir / "distancias_enderecos_parte2_bellman_ford.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        w = csv.writer(file)
        w.writerow(["origem", "destino", "custo", "caminho"])
        w.writerows(resultados)

    tempo_total = time() - inicio_total

    if tempos_calculo:
        tempo_medio = sum(tempos_calculo) / len(tempos_calculo)
        tempo_max = max(tempos_calculo)
        tempo_min = min(tempos_calculo)
    else:
        tempo_medio = tempo_max = tempo_min = 0.0

    _ = tempo_construcao, tempo_total, tempo_medio, tempo_max, tempo_min, estatisticas, arestas_lidas, arestas_negativas
