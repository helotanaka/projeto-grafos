import csv, json, unicodedata, re
from pathlib import Path
from time import time
import tracemalloc

from src.graphs.graph import Graph
from src.graphs.algorithms import (
    bellman_ford_path,
    bellman_ford_path_length,
    NoPath,
    NegativeCycle,
    NodeNotFound,
)

def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower())
    return s.strip("_")

def verificar_ciclo_no_caminho(caminho):

    if not caminho or len(caminho) < 2:
        return "sem_ciclo", None
    
    if caminho[0] == caminho[-1]:
        return "ciclo_completo", caminho
    
    nos_visitados = {}
    for i, no in enumerate(caminho):
        if no in nos_visitados:
            inicio_ciclo = nos_visitados[no]
            subciclo = caminho[inicio_ciclo:i+1]
            
            if inicio_ciclo == 0 and i == len(caminho) - 1:
                return "ciclo_completo", subciclo
            else:
                return "caminho_com_ciclo", subciclo
        nos_visitados[no] = i
    
    return "sem_ciclo", None

def analisar_ciclo_negativo(G, caminho, custo, origem, destino, excecao_ciclo=False):
    if excecao_ciclo:
        tipo_estrutural, _ = verificar_ciclo_no_caminho(caminho)
        
        if tipo_estrutural == "ciclo_completo":
            return True
        else:
            return False
    
    if custo is not None and custo < 0:
        tipo_estrutural, _ = verificar_ciclo_no_caminho(caminho)
        
        if tipo_estrutural == "ciclo_completo":
            return True
        
        if caminho and len(caminho) >= 2:
            ultimo_no = caminho[-1]
            primeiro_no = caminho[0]
            
            try:
                vizinhos_do_ultimo = [v for v, _ in G.vizinhos(ultimo_no)]
                if primeiro_no in vizinhos_do_ultimo:
                    return True
            except:
                pass
        
        return False
    
    return False

def calcular_distancias_bellman_ford():
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
        tracemalloc.stop()
        return

    resultados = []
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

                custo = None
                caminho = []
                tem_ciclo_negativo = False
                excecao_ciclo_negativo = False

                if not G.tem_no(origem):
                    print(f"[{idx}/{total_rotas}] Origem não existe: {origem}")
                    resultados.append([origem, destino, custo, ""])
                    continue

                elif not G.tem_no(destino):
                    print(f"[{idx}/{total_rotas}] Destino não existe: {destino}")
                    resultados.append([origem, destino, custo, ""])
                    continue

                else:
                    inicio_rota = time()
                    timeout_segundos = 30

                    try:
                        custo = bellman_ford_path_length(G, origem, destino)

                        if time() - inicio_rota > timeout_segundos:
                            raise TimeoutError(f"Timeout de {timeout_segundos}s atingido")

                        caminho = bellman_ford_path(G, origem, destino)
                        
                        tem_ciclo_negativo = analisar_ciclo_negativo(
                            G, caminho, custo, origem, destino, excecao_ciclo_negativo
                        )

                        tempo_rota = time() - inicio_rota
                        tempos_calculo.append(tempo_rota)

                    except NegativeCycle as e:
                        excecao_ciclo_negativo = True
                        custo = e.cost if hasattr(e, "cost") else None
                        caminho = e.path if hasattr(e, "path") else []

                        tem_ciclo_negativo = analisar_ciclo_negativo(
                            G, caminho, custo, origem, destino, excecao_ciclo_negativo
                        )

                        tempo_rota = time() - inicio_rota
                        tempos_calculo.append(tempo_rota)

                        if caminho:
                            print(f"    Caminho: {' -> '.join(caminho[:5])}...")
                        if custo is not None:
                            try:
                                print(f"    Custo: {float(custo):.2f}")
                            except (TypeError, ValueError):
                                print(f"    Custo: {custo}")

                    except NoPath:
                        print(f"[{idx}/{total_rotas}] Sem caminho: {origem} → {destino}")

                    except NodeNotFound as e:
                        print(f"[{idx}/{total_rotas}] Nó não encontrado: {e}")

                    except TimeoutError:
                        print(f"[{idx}/{total_rotas}] TIMEOUT: {origem} → {destino}")
                        print("    Rota demorou mais de 30s - possível ciclo negativo complexo")

                    except Exception as e:
                        print(f"[{idx}/{total_rotas}] Erro desconhecido: {e}")

                caminho_str = " -> ".join(caminho) if caminho else ""

                resultados.append([origem, destino, custo, caminho_str])

                json_name = f"percurso_{_slug(origem)}_{_slug(destino)}.json"
                json_data = {
                    "origem": origem,
                    "destino": destino,
                    "custo": custo,
                    "caminho": caminho,
                    "tem_ciclo_negativo": tem_ciclo_negativo,
                }
                
                with open(json_dir / json_name, "w", encoding="utf-8") as jf:
                    json.dump(json_data, jf, ensure_ascii=False, indent=2)

    except FileNotFoundError:
        print("ERRO: Arquivo de endereços não encontrado.")
        tracemalloc.stop()
        return

    csv_path = json_dir / "distancias_enderecos_parte2_bellman_ford.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        w = csv.writer(file)
        w.writerow(["origem", "destino", "custo", "caminho"])
        w.writerows(resultados)

    tempo_total = time() - inicio_total
    memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    report_path = json_dir / "parte2_report.json"
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except FileNotFoundError:
        report = {}

    report["bellman_ford_parte2"] = {
        "tempo": tempo_total,
        "memoria": memoria_pico,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)