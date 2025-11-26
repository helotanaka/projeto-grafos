# Disciplina de Grafos - CESAR School 2025.2

Instalar os requirements utilizando: 
```bash
pip install -r requirements.txt
```
## Primeira parte: Grafo dos Bairros do Recife
1) Processar e normalizar bairros:
```bash
python -m src.graphs.io
```
2) Calcular métricas globais, microrregiões e ego:
```bash
python -m src.global_metrics_calculator
```
4) Gerar análises específicas:
```bash
python -m src.get_bairro-grau
```
```bash
python -m src.get_bairro_maior_grau
```
```bash
python -m src.get_bairro_mais_denso
```
6) Executar Dijkstra para todos os endereços:
```bash
python -m src.cli --calc-enderecos
```
8) Gerar a árvore do percurso obrigatório:
```bash
python -m src.gerar_arvore_percurso
```
9) Gerar grafo interativo em HTML:
```bash
python -m src.cli --grafo-interativo
```
10) Visualizações :
```bash
python -m src.run_viz
```
Colocar o path do grafo interativo no browser para vizualizar

## Segunda parte: Ligações Rodoviárias e Hidroviárias (IBGE 2016)
1) Rodar BFS direcionado:
```bash
python -m src.cli --bfs
```
2) Rodar DFS direcionado:
```bash
python -m src.cli --dfs
```
3) Executar testes de Dijkstra + Bellman–Ford:
```bash
python -B -m tests.cli_parte2 --calc-enderecos-parte2
```
