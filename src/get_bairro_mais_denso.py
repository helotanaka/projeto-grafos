import pandas as pd

egoBairro = pd.read_csv("out/ego_bairro.csv")

bigger_densidade_ego = 0

dados = {
  "bairro": [],
  "densidade_ego": []
}
for _, linha in egoBairro.iterrows():
    bairro = linha['bairro']
    densidade_ego = linha['densidade_ego']
    
    if(densidade_ego > bigger_densidade_ego):
        bigger_densidade_ego = densidade_ego

for _, linha in egoBairro.iterrows():
    bairro = linha['bairro']
    densidade_ego = linha['densidade_ego']
    
    if(densidade_ego == bigger_densidade_ego):
        dados['bairro'].append(bairro)
        dados['densidade_ego'].append(densidade_ego)

df_final = pd.DataFrame(dados)
df_final.to_csv("out/bairro_mais_denso.csv", index=False, encoding="utf-8")