import pandas as pd
import unicodedata

dt = pd.read_csv("data/bairros_recife.csv")

dados = {
  "bairro": [],
  "microrregiao": []
}

def montarDataframe(dt):
  for i in range(dt.shape[1]):  # pega cada coluna
    microrregiao = dt.columns[i]  
        
    for bairro in dt.iloc[:, i]:  # cada linha  
      if pd.notna(bairro):  # ignora valores vazios
        dados["bairro"].append(normalizarNome(bairro))
        dados["microrregiao"].append(microrregiao)

def normalizarNome(bairro):
  texto = unicodedata.normalize("NFKD", bairro)
  texto = "".join(c for c in texto if not unicodedata.combining(c))
  return texto.replace("ç", "c").strip().lower()

montarDataframe(dt) 

df_final = pd.DataFrame(dados)
df_final.to_csv("out/bairros_unique.csv", index=False, encoding="utf-8")
