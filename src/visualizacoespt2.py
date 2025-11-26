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
    
    plt.xticks(range(0, int(max(graus_totais)) + 100, 100)) 
    plt.yticks(range(0, int(max(plt.gca().get_ylim())) + 250, 250))
    
    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, 'distribuicao_graus.png')
    
    plt.savefig(output_file)
    
    print(f'Gráfico salvo em: {output_file}')
    
    plt.close()

file_path = 'data/dataset_parte2/LRH2016_00_Base_Completa.csv'

output_path = 'out/visualizacoespt2'

load_and_plot_degrees(file_path, output_path)

