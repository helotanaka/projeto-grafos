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

def gerar_grafo_interativo():

    from pyvis.network import Network  # import local pra não quebrar quem não usa o interativo
    import json as _json

    base = Path(__file__).resolve().parent.parent   # raiz do projeto
    data_dir = base / "data"
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)

    # ---------- 1) Monta o grafo a partir de adjacencias_bairros.csv ----------
    G = Graph()
    label_map = {}  # nome_normalizado -> nome_original (com acento/capitalização)

    with open(data_dir / "adjacencias_bairros.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_raw = r["bairro_origem"].strip()
            v_raw = r["bairro_destino"].strip()
            w = float(r["peso"])

            u = _normalize(u_raw)
            v = _normalize(v_raw)

            G.adicionar_aresta(u, v, w)

            # guarda nome "bonito" pra tooltip/label
            label_map.setdefault(u, u_raw)
            label_map.setdefault(v, v_raw)

    # ---------- 2) Mapeia bairro -> microrregiao usando bairros_recife.csv ----------
    microrregioes = {}  # nome_normalizado -> microrregiao (ex.: "1.1")
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
        # se não achar o CSV, segue sem microrregião (fica "?")
        pass

    # ---------- 3) Calcula grau e densidade da ego-subrede ----------
    def _densidade_ego(no: str) -> float:
        """
        Ego-subrede: nó + vizinhos.
        Densidade = arestas_entre_vizinhos / max_arestas_possiveis_entre_vizinhos
        (grafo não-direcionado)
        """
        vizinhos = [v for v, _w in G.vizinhos(no)]
        k = len(vizinhos)
        if k <= 1:
            return 0.0

        viz_set = set(vizinhos)
        # conta arestas entre vizinhos (sem contar 2x)
        edges = 0
        for i in range(k):
            vi = vizinhos[i]
            viz_vi = {x for x, _w in G.vizinhos(vi)} & viz_set
            for j in range(i + 1, k):
                vj = vizinhos[j]
                if vj in viz_vi:
                    edges += 1

        max_edges = k * (k - 1) / 2
        return float(edges) / max_edges if max_edges > 0 else 0.0

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

    # ---------- 4) Carrega percurso Nova Descoberta -> Setúbal ----------
    caminho_nodes = []
    try:
        with open(out_dir / "percurso_nova_descoberta_setubal.json", encoding="utf-8") as jf:
            dados_percurso = json.load(jf)
            # caminho no JSON já vem em lower/sem acento (foi salvo a partir do grafo)
            caminho_nodes = [_normalize(b) for b in dados_percurso.get("caminho", [])]
    except FileNotFoundError:
        # se não existir, segue sem destaque de caminho
        caminho_nodes = []

    # constrói lista de IDs de arestas do percurso (vamos usar na legenda/botão)
    path_edge_ids = []
    for i in range(len(caminho_nodes) - 1):
        u = caminho_nodes[i]
        v = caminho_nodes[i + 1]
        a, b = sorted([u, v])
        path_edge_ids.append(f"{a}__{b}")

    # ---------- 5) Monta o grafo interativo com pyvis ----------
    default_node_color = "#97C2FC"
    default_edge_color = "#848484"

    net = Network(height="750px", width="100%", notebook=False, directed=False)
    net.barnes_hut()

    # adiciona nós com tooltip
    for u, info in stats.items():
        tooltip = (
            f"<b>{info['label']}</b><br>"
            f"Microrregião: {info['microrregiao']}<br>"
            f"Grau: {info['grau']}<br>"
            f"Densidade ego: {info['densidade_ego']:.3f}"
        )
        net.add_node(
            u,  # id = nome normalizado
            label=info["label"],  # nome bonito
            title=tooltip,
            value=info["grau"],   # controla o tamanho do nó
            color=default_node_color,
        )

    # adiciona arestas (sem duplicar, já que o grafo é não-direcionado)
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

    # ---------- 6) Injeta caixa de busca + checkbox de destaque do percurso ----------
    controles_html = """
    <div style="margin: 10px 0; font-family: Arial, sans-serif;">
      <input id="searchBox" type="text" placeholder="Buscar bairro..."
             style="padding:4px; width:220px; margin-right:8px;" />
      <button onclick="searchNode()" style="padding:4px 10px;">Buscar</button>
      <label style="margin-left:20px; font-size:14px;">
        <input type="checkbox" id="togglePath" onchange="togglePathHighlight()" />
        Destacar percurso Nova Descoberta → Boa Viagem (Setúbal)
      </label>
    </div>
    """

    path_nodes_js = _json.dumps(caminho_nodes)
    path_edges_js = _json.dumps(path_edge_ids)

    extra_script = f"""
    <script type="text/javascript">
      var pathNodeIds = {path_nodes_js};
      var pathEdgeIds = {path_edges_js};
      var defaultNodeColor = "{default_node_color}";
      var defaultEdgeColor = "{default_edge_color}";
      var pathHighlighted = false;

      function searchNode() {{
        var q = document.getElementById('searchBox').value.toLowerCase().trim();
        if (!q) return;

        var allNodes = nodes.get();
        var target = null;

        for (var i = 0; i < allNodes.length; i++) {{
          var label = String(allNodes[i].label || allNodes[i].id).toLowerCase();
          if (label.indexOf(q) !== -1) {{
            target = allNodes[i];
            break;
          }}
        }}

        if (target) {{
          network.focus(target.id, {{
            scale: 1.5,
            animation: {{
              duration: 800,
              easing: 'easeInOutQuad'
            }}
          }});
          network.selectNodes([target.id]);
        }} else {{
          alert("Nenhum bairro encontrado para: " + q);
        }}
      }}

      function togglePathHighlight() {{
        pathHighlighted = !pathHighlighted;

        if (!pathNodeIds || pathNodeIds.length === 0) {{
          console.log("Nenhum percurso carregado.");
          return;
        }}

        if (pathHighlighted) {{
          var nodeUpdates = [];
          for (var i = 0; i < pathNodeIds.length; i++) {{
            nodeUpdates.push({{id: pathNodeIds[i], color: {{background: '#ff9900'}} }});
          }}
          nodes.update(nodeUpdates);

          var edgeUpdates = [];
          for (var j = 0; j < pathEdgeIds.length; j++) {{
            edgeUpdates.push({{
              id: pathEdgeIds[j],
              color: {{color: '#ff0000'}},
              width: 4
            }});
          }}
          edges.update(edgeUpdates);
        }} else {{
          var nodeUpdates = [];
          for (var i = 0; i < pathNodeIds.length; i++) {{
            nodeUpdates.push({{id: pathNodeIds[i], color: {{background: defaultNodeColor}} }});
          }}
          nodes.update(nodeUpdates);

          var edgeUpdates = [];
          for (var j = 0; j < pathEdgeIds.length; j++) {{
            edgeUpdates.push({{
              id: pathEdgeIds[j],
              color: {{color: defaultEdgeColor}},
              width: 1
            }});
          }}
          edges.update(edgeUpdates);
        }}
      }}
    </script>
    """

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

    print(f"Grafo interativo salvo em: {saida}")