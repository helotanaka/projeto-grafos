import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import os
from pyvis.network import Network
import numpy as np
import seaborn as sns

def load_and_plot_degrees(file_path, output_path):
    df = pd.read_csv(file_path)
    
    edges = df[['uf_a', 'codmundv_a', 'nomemun_a', 'uf_b', 'codmundv_b', 'nomemun_b', 'tempo']]
    edges.columns = ['origem_uf', 'origem_cod', 'origem_nome', 'destino_uf', 'destino_cod', 'destino_nome', 'peso']
    
    grau_origem = edges['origem_nome'].value_counts()
    grau_destino = edges['destino_nome'].value_counts()
    graus_totais = grau_origem.add(grau_destino, fill_value=0)
    
    plt.figure(figsize=(10, 6))
    plt.hist(graus_totais, bins=50, color='skyblue', edgecolor='black')
    plt.title('Distribuição de Graus dos Nós', fontsize=16)
    plt.xlabel('Grau (Número de Conexões)', fontsize=12)
    plt.ylabel('Frequência', fontsize=12)
    plt.grid(True)
    
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, 'distribuicao_graus.png')
    
    plt.savefig(output_file)
    
    print(f'Gráfico salvo em: {output_file}')
    
    plt.close()

file_path = 'data/dataset_parte2/LRH2016_00_Base_Completa.csv'

output_path = 'out/visualizacoespt2'

load_and_plot_degrees(file_path, output_path)

def create_distance_heatmap(file_path, output_path):
    df = pd.read_csv(file_path)
    
    edges = df[['uf_a', 'codmundv_a', 'nomemun_a', 'uf_b', 'codmundv_b', 'nomemun_b', 'tempo']]
    edges.columns = ['origem_uf', 'origem_cod', 'origem_nome', 'destino_uf', 'destino_cod', 'destino_nome', 'peso']
    
    nodes = pd.concat([edges['origem_nome'], edges['destino_nome']]).unique()
    node_idx = {node: idx for idx, node in enumerate(nodes)}
    
    dist_matrix = np.zeros((len(nodes), len(nodes)))
    for _, row in edges.iterrows():
        origem_idx = node_idx[row['origem_nome']]
        destino_idx = node_idx[row['destino_nome']]
        dist_matrix[origem_idx, destino_idx] = row['peso']
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(dist_matrix, xticklabels=nodes, yticklabels=nodes, cmap="YlGnBu", annot=False, fmt="g")
    plt.title('Heatmap de Distâncias (Tempo) entre os Nós', fontsize=16)
    plt.xlabel('Destino', fontsize=12)
    plt.ylabel('Origem', fontsize=12)
    
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, 'heatmap_distancias.png')
    
    plt.savefig(output_file)
    
    print(f'Heatmap de distâncias salvo em: {output_file}')
    
    plt.close()

file_path = 'data/dataset_parte2/LRH2016_00_Base_Completa.csv'

output_path = 'out/visualizacoespt2'
create_distance_heatmap(file_path, output_path)


def load_and_create_graph(file_path, output_path):
    df = pd.read_csv(file_path)
    
    edges = df[['uf_a', 'codmundv_a', 'nomemun_a', 'uf_b', 'codmundv_b', 'nomemun_b', 'tempo']]
    edges.columns = ['origem_uf', 'origem_cod', 'origem_nome', 'destino_uf', 'destino_cod', 'destino_nome', 'peso']
    
    net = Network(height='750px', width='100%', directed=True)
    for _, row in edges.iterrows():
        net.add_node(row['origem_nome'], label=row['origem_nome'])
        net.add_node(row['destino_nome'], label=row['destino_nome'])
        net.add_edge(row['origem_nome'], row['destino_nome'], value=row['peso'])

    os.makedirs(output_path, exist_ok=True)
    
    output_file = os.path.join(output_path, 'amostra_grafo.html')
    net.save_graph(output_file)
    
    print(f'Grafo salvo em: {output_file}')

file_path = 'data/dataset_parte2/LRH2016_00_Base_Completa.csv'

output_path = 'out/visualizacoespt2'

load_and_create_graph(file_path, output_path)
