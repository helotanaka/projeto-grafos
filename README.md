# Projeto da Disciplina de Grafos - CESAR School 2025.2

 Instalar os requirements utilizando: *pip install -r requirements.txt*

## Primeira parte: Grafo dos Bairros do Recife
1) Processar e normalizar bairros: *python -m src.graphs.io*
3) Calcular métricas globais, microrregiões e ego: *python -m src.global_metrics_calculator*
4) Gerar análises específicas:
    *python -m src.get_bairro-grau*
    *python -m src.get_bairro_maior_grau*
    *python -m src.get_bairro_mais_denso*
5) Executar Dijkstra para todos os endereços: *python -m src.cli --calc-enderecos*
6) Gerar a árvore do percurso obrigatório: *python -m src.gerar_arvore_percurso*
7) Gerar grafo interativo em HTML: *python -m src.cli --grafo-interativo*
8) Visualizações : *python -m src.run_viz*

## Segunda parte: Ligações Rodoviárias e Hidroviárias (IBGE 2016)
1) Rodar BFS direcionado: *python -m src.cli --bfs*
2) Rodar DFS direcionado: *python -m src.cli --dfs*
3) Executar testes de Dijkstra + Bellman–Ford: *python -B -m tests.cli_parte2 --calc-enderecos-parte2*
4) Executar as visualizações: *python -m src.visualizacoespt2*
