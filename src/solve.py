import csv, json, unicodedata, re
from pathlib import Path
from .graphs.graph import Graph
from .graphs.algorithms import dijkstra_path, dijkstra_path_length,  bfs_ordem_camadas_ciclos_dir,  dfs_ordem_camadas_ciclos_dir


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

            if not G.tem_no(bx_norm):
                raise KeyError(f"Bairro_X '{bx_raw}' não existe no grafo (normalizado: '{bx_norm}').")
            if not G.tem_no(by_norm):
                raise KeyError(f"Bairro_Y '{by_raw}' não existe no grafo (normalizado: '{by_norm}').")

            custo = dijkstra_path_length(G, bx_norm, by_norm)
            caminho = dijkstra_path(G, bx_norm, by_norm)

            resultados.append([end_x, end_y, bx_raw, by_raw, custo, " -> ".join(caminho)])

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

    with open(out_dir / "distancias_enderecos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["X", "Y", "bairro_X", "bairro_Y", "custo", "caminho"])
        w.writerows(resultados)

def gerar_grafo_interativo():

    from pyvis.network import Network
    import json as _json

    base = Path(__file__).resolve().parent.parent
    data_dir = base / "data"
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)

    G = Graph()
    label_map = {}
    adj = {}

    with open(data_dir / "adjacencias_bairros.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_raw = r["bairro_origem"].strip()
            v_raw = r["bairro_destino"].strip()
            w = float(r["peso"])

            u = _normalize(u_raw)
            v = _normalize(v_raw)

            G.adicionar_aresta(u, v, w)

            label_map.setdefault(u, u_raw)
            label_map.setdefault(v, v_raw)

            adj.setdefault(u, []).append((v, w))
            adj.setdefault(v, []).append((u, w))

    microrregioes = {}
    try:
        with open(data_dir / "bairros_recife.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            campos = reader.fieldnames or []
            for row in reader:
                for col in campos:
                    bairro_bruto = (row.get(col) or "").strip()
                    if not bairro_bruto:
                        continue
                    b_norm = _normalize(bairro_bruto)
                    # se aparecer mais de uma vez, mantém a primeira microrregião
                    microrregioes.setdefault(b_norm, col)
    except FileNotFoundError:
        pass

    def _densidade_ego(no: str) -> float:

        vizinhos = [v for v, _w in G.vizinhos(no)]
        vizinhos.append(no)

        num_nos_ego = len(vizinhos)

        if num_nos_ego < 2:
            return 0.0

        arestas = 0
        for i in range(num_nos_ego):
            for j in range(i + 1, num_nos_ego):
                u, v = sorted([vizinhos[i], vizinhos[j]])
                if v in G.adj.get(u, {}):
                    arestas += 1

        # Calcula a densidade com a fórmula que ta no pdf da laura
        densidade = (2 * arestas) / (num_nos_ego * (num_nos_ego - 1))

        return densidade

    stats = {}  # nome_normalizado -> dict com grau, microrregiao, densidade_ego, label
    for u in G.nos():
        grau = G.grau(u)
        dens = _densidade_ego(u)
        mic = microrregioes.get(u, "?")
        label = label_map.get(u, u)
        stats[u] = {
            "grau": grau,
            "densidade_ego": dens,
            "microrregiao": mic,
            "label": label,
        }

    default_node_color = "#97C2FC"
    default_edge_color = "#848484"

    mic_set = sorted({info["microrregiao"] for info in stats.values()})
    palette = [
        "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
        "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999",
    ]
    mic_colors = {}
    for idx, mic in enumerate(mic_set):
        if mic == "?":
            mic_colors[mic] = default_node_color
        else:
            mic_colors[mic] = palette[idx % len(palette)]

    original_node_colors = {
        u: mic_colors.get(info["microrregiao"], default_node_color)
        for u, info in stats.items()
    }

    caminho_nodes = []
    try:
        with open(out_dir / "percurso_nova_descoberta_setubal.json", encoding="utf-8") as jf:
            dados_percurso = _json.load(jf)
            caminho_nodes = [_normalize(b) for b in dados_percurso.get("caminho", [])]
    except FileNotFoundError:
        caminho_nodes = []

    net = Network(height="750px", width="100%", notebook=False, directed=False)
    net.barnes_hut()

    # tooltip e cor por microrregião
    for u, info in stats.items():
        tooltip = (
            f"Bairro: {info['label']}; "
            f"Microrregião: {info['microrregiao']}; "
            f"Grau: {info['grau']}; "
            f"Densidade ego: {info['densidade_ego']:.3f}"
        )
        net.add_node(
            u,
            label=info["label"],
            title=tooltip,
            value=info["grau"],
            color=original_node_colors.get(u, default_node_color),
        )

    edges_seen = set()
    for u in G.nos():
        for v, w in G.vizinhos(u):
            a, b = sorted([u, v])
            key = (a, b)
            if key in edges_seen:
                continue
            edges_seen.add(key)
            edge_id = f"{a}__{b}"
            net.add_edge(
                u,
                v,
                id=edge_id,
                value=w,
                color=default_edge_color,
                width=1,
            )

    net.set_options("""
    {
    "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
    },
    "nodes": {
        "shape": "dot",
        "scaling": {
        "min": 5,
        "max": 20
        }
    },
    "physics": {
        "stabilization": true
    }
    }
        """)

    html = net.generate_html(notebook=False)

    bairros_lista = sorted(
        [(info["label"], u) for u, info in stats.items()],
        key=lambda x: x[0].lower()
    )
    options_html = "\n".join(
        f'<option value="{u}">{label}</option>' for label, u in bairros_lista
    )

    controles_html = f"""
    <div style="margin: 10px 0; font-family: Arial, sans-serif;">
      <input id="searchBox" type="text" placeholder="Buscar bairro..."
             style="padding:4px; width:220px; margin-right:8px;" />
      <button onclick="searchNode()" style="padding:4px 10px;">Buscar</button>
      <br style="margin-top:8px;" />
      <label style="font-size:14px; margin-right:4px;">Entrada:</label>
      <select id="origemSelect" style="padding:4px; min-width:180px;">
        <option value="">-- selecione --</option>
        {options_html}
      </select>
      <label style="font-size:14px; margin:0 4px 0 12px;">Saída:</label>
      <select id="destinoSelect" style="padding:4px; min-width:180px;">
        <option value="">-- selecione --</option>
        {options_html}
      </select>
      <button onclick="filtrarEntradaSaida()" style="padding:4px 10px; margin-left:8px;">Filtrar caminho</button>
      <label style="margin-left:20px; font-size:14px;">
        <input type="checkbox" id="togglePath" onchange="togglePathHighlight()" />
        Destacar percurso Nova Descoberta → Boa Viagem (Setúbal)
      </label>
    </div>
    """

    path_nodes_js = _json.dumps(caminho_nodes)
    adj_js = _json.dumps(adj)
    orig_colors_js = _json.dumps(original_node_colors)

    extra_script_template = """
    <script type="text/javascript">
      var defaultPathNodes = __PATH_NODES__;
      var defaultEdgeColor = "__EDGE_COLOR__";
      var originalNodeColors = __ORIG_COLORS__;
      var graphAdj = __ADJ__;

      function searchNode() {
        var q = document.getElementById('searchBox').value.toLowerCase().trim();
        if (!q) return;

        var allNodes = nodes.get();
        var target = null;

        for (var i = 0; i < allNodes.length; i++) {
          var label = String(allNodes[i].label || allNodes[i].id).toLowerCase();
          if (label.indexOf(q) !== -1) {
            target = allNodes[i];
            break;
          }
        }

        if (target) {
          network.focus(target.id, {
            scale: 1.5,
            animation: {
              duration: 800,
              easing: 'easeInOutQuad'
            }
          });
          network.selectNodes([target.id]);
        } else {
          alert("Nenhum bairro encontrado para: " + q);
        }
      }

      function highlightPath(pathNodes) {
        // reseta cores originais
        var nodeUpdates = [];
        for (var id in originalNodeColors) {
          nodeUpdates.push({id: id, color: {background: originalNodeColors[id]}});
        }
        nodes.update(nodeUpdates);

        var allEdges = edges.get();
        var edgeUpdates = [];
        for (var i = 0; i < allEdges.length; i++) {
          edgeUpdates.push({
            id: allEdges[i].id,
            color: {color: defaultEdgeColor},
            width: 1
          });
        }
        edges.update(edgeUpdates);

        if (!pathNodes || pathNodes.length === 0) {
          return;
        }

        // destaca nós do caminho
        var pathNodeUpdates = [];
        for (var j = 0; j < pathNodes.length; j++) {
          pathNodeUpdates.push({
            id: pathNodes[j],
            color: {background: '#ff9900'}
          });
        }
        nodes.update(pathNodeUpdates);

        // destaca arestas do caminho
        var pathEdgeUpdates = [];
        for (var k = 0; k < pathNodes.length - 1; k++) {
          var a = pathNodes[k];
          var b = pathNodes[k + 1];
          var pair = [a, b].sort();
          var eid = pair[0] + "__" + pair[1];
          pathEdgeUpdates.push({
            id: eid,
            color: {color: '#ff0000'},
            width: 4
          });
        }
        edges.update(pathEdgeUpdates);
      }

      function togglePathHighlight() {
        var cb = document.getElementById('togglePath');
        if (!cb) return;
        if (cb.checked) {
          if (!defaultPathNodes || defaultPathNodes.length === 0) {
            alert("Percurso Nova Descoberta → Setúbal não encontrado.");
            cb.checked = false;
            return;
          }
          highlightPath(defaultPathNodes);
          network.fit({
            nodes: defaultPathNodes,
            animation: {
              duration: 800,
              easing: 'easeInOutQuad'
            }
          });
        } else {
          highlightPath([]);
        }
      }

      function shortestPath(origem, destino) {
        if (!graphAdj[origem] || !graphAdj[destino]) {
          return [];
        }
        var dist = {};
        var prev = {};
        var visited = {};
        var nodesList = Object.keys(graphAdj);
        for (var i = 0; i < nodesList.length; i++) {
          var n = nodesList[i];
          dist[n] = Infinity;
          prev[n] = null;
          visited[n] = false;
        }
        dist[origem] = 0;

        for (var count = 0; count < nodesList.length; count++) {
          var u = null;
          var best = Infinity;
          for (var i = 0; i < nodesList.length; i++) {
            var n = nodesList[i];
            if (!visited[n] && dist[n] < best) {
              best = dist[n];
              u = n;
            }
          }
          if (u === null) break;
          if (u === destino) break;
          visited[u] = true;

          var neigh = graphAdj[u] || [];
          for (var j = 0; j < neigh.length; j++) {
            var v = neigh[j][0];
            var w = neigh[j][1];
            var alt = dist[u] + w;
            if (alt < dist[v]) {
              dist[v] = alt;
              prev[v] = u;
            }
          }
        }

        var path = [];
        var curr = destino;
        if (curr !== origem && prev[curr] == null) {
          return [];
        }
        while (curr != null) {
          path.unshift(curr);
          if (curr === origem) break;
          curr = prev[curr];
        }
        return path;
      }

      function filtrarEntradaSaida() {
        var origem = document.getElementById('origemSelect').value;
        var destino = document.getElementById('destinoSelect').value;
        if (!origem || !destino) {
          alert("Selecione um bairro de entrada e um de saída.");
          return;
        }
        var path = shortestPath(origem, destino);
        if (!path || path.length === 0) {
          alert("Não foi encontrado caminho entre os bairros selecionados.");
          return;
        }
        highlightPath(path);
        network.fit({
          nodes: path,
          animation: {
            duration: 800,
            easing: 'easeInOutQuad'
          }
        });
      }
    </script>
    """

    extra_script = (
        extra_script_template
        .replace("__PATH_NODES__", path_nodes_js)
        .replace("__EDGE_COLOR__", default_edge_color)
        .replace("__ORIG_COLORS__", orig_colors_js)
        .replace("__ADJ__", adj_js)
    )

    if "<body>" in html:
        html = html.replace("<body>", "<body>\n" + controles_html, 1)
    else:
        html = controles_html + html

    if "</body>" in html:
        html = html.replace("</body>", extra_script + "\n</body>", 1)
    else:
        html = html + extra_script

    saida = out_dir / "grafo_interativo.html"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)




def bfs():
    base = Path(__file__).resolve().parent.parent 
    data_dir = base /"data"/"dataset_parte2"
    out_dir = base /"out"/ "parte2"/ "BFS"
    out_dir.mkdir(parents=True, exist_ok=True)

    G = Graph()
    with open(data_dir / "LRH2016_00_Base_Completa.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mun_a = (row.get("nomemun_a") or "").strip()
            mun_b = (row.get("nomemun_b") or "").strip()

            if not mun_a or not mun_b:
                continue

            custo_str = (row.get("custo") or "").strip()
            if not custo_str:
                continue

            try:
                custo = float(custo_str)
            except ValueError:
                continue

            G.adicionar_aresta(mun_a, mun_b, custo)

    with open(data_dir / "enderecos_parte2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            inicio = (row.get("municipio_inicio") or "").strip().strip('"')
            destino = (row.get("municipio_destino") or "").strip().strip('"')

            if not inicio:
                continue

            print(f"\n[BFS] Origem: '{inicio}'  Destino (apenas para nome do arquivo): '{destino}'")

            if not G.tem_no(inicio):
                resultado = {
                    "fonte": inicio,
                    "destino": destino,
                    "erro": f"Município '{inicio}' não existe no grafo construído a partir do dataset.",
                }
            else:
                ordem, camadas, ciclos = bfs_ordem_camadas_ciclos_dir(
                    G,
                    inicio,
                    max_cycles=10,
                )
                resultado = {
                    "fonte": inicio,
                    "destino": destino,
                    "ordem": ordem,
                    "camadas": camadas,
                    "ciclos": ciclos,
                }

                print(f"Ordem: {len(ordem)} nós visitados")
                print(f"Camadas: {len(camadas)} níveis")
                print(f"Ciclos armazenados: {len(ciclos)}")

            nome_arquivo = f"bfs_{inicio}_{destino}.json"
            arquivo_saida = out_dir / nome_arquivo

            with open(arquivo_saida, "w", encoding="utf-8") as jf:
                json.dump(resultado, jf, ensure_ascii=False, indent=2)

            print(f"JSON salvo em: {arquivo_saida}")

def dfs():
    base = Path(__file__).resolve().parent.parent
    data_dir = base / "data" / "dataset_parte2"
    out_dir = base / "out" / "parte2"/ "DFS"
    out_dir.mkdir(parents=True, exist_ok=True)

    G = Graph()
    with open(data_dir / "LRH2016_00_Base_Completa.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mun_a = (row.get("nomemun_a") or "").strip()
            mun_b = (row.get("nomemun_b") or "").strip()

            if not mun_a or not mun_b:
                continue

            custo_str = (row.get("custo") or "").strip()
            if not custo_str:
                continue

            try:
                custo = float(custo_str)
            except ValueError:
                continue

            G.adicionar_aresta(mun_a, mun_b, custo)

    with open(data_dir / "enderecos_parte2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            inicio = (row.get("municipio_inicio") or "").strip().strip('"')
            destino = (row.get("municipio_destino") or "").strip().strip('"')

            if not inicio:
                continue

            print(f"\n[DFS] Origem: '{inicio}'  Destino (apenas para nome do arquivo): '{destino}'")

            if not G.tem_no(inicio):
                resultado = {
                    "fonte": inicio,
                    "destino": destino,
                    "erro": f"Município '{inicio}' não existe no grafo construído a partir do dataset.",
                }
            else:
                ordem, camadas, ciclos = dfs_ordem_camadas_ciclos_dir(
                    G,
                    inicio,
                    max_cycles=10,
                )
                resultado = {
                    "fonte": inicio,
                    "destino": destino,
                    "ordem": ordem,
                    "camadas": camadas,
                    "ciclos": ciclos,
                }

                print(f"Ordem: {len(ordem)} nós visitados")
                print(f"Camadas (profundidade DFS): {len(camadas)} níveis")
                print(f"Ciclos armazenados: {len(ciclos)}")

            nome_arquivo = f"dfs_{inicio}_{destino}.json"
            arquivo_saida = out_dir / nome_arquivo

            with open(arquivo_saida, "w", encoding="utf-8") as jf:
                json.dump(resultado, jf, ensure_ascii=False, indent=2)
