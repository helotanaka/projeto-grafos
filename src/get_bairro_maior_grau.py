import pandas as pd

egoBairro = pd.read_csv("out/ego_bairro.csv")

bigger_grau = 0

dados = {
  "bairro": [],
  "grau": []
}
for _, linha in egoBairro.iterrows():
    bairro = linha['bairro']
    grau = linha['grau']
    
    if(grau > bigger_grau):
        bigger_grau = grau

for _, linha in egoBairro.iterrows():
    bairro = linha['bairro']
    grau = linha['grau']
    
    if(grau == bigger_grau):
        dados['bairro'].append(bairro)
        dados['grau'].append(grau)

df_final = pd.DataFrame(dados)
df_final.to_csv("out/bairro_maior_grau.csv", index=False, encoding="utf-8")