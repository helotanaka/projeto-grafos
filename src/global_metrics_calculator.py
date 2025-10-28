import pandas as pd

def calcularDensidade(ordem, tamanho):
  if ordem < 2:
    return 0
  
  return (2 * tamanho)/(ordem * (ordem - 1))

# CIDADE DO RECIFE

dtBairros = pd.read_csv("out/bairros_unique.csv")
dtArestas = pd.read_csv("data/adjacencias_bairros.csv")

ordem = dtBairros.shape[0]
tamanho = dtArestas.shape[0]

dadosRecife = {
  "ordem": [ordem],
  "tamanho": [tamanho],
  "densidade": [calcularDensidade(ordem, tamanho)]
}

dfRecife = pd.DataFrame(dadosRecife)
dfRecife.to_json("out/recife_global.json", orient="records", indent=4, force_ascii=False)

#MICRORREGIÕES

dadosMicros = {
  "microrregiao": [],
  "ordem": [],
  "tamanho": [],
  "densidade": []
}

def listarBairros(numero):
    bairros = []

    alvo = int(numero)

    for _, linha in dtBairros.iterrows():
        valorMicro = linha["microrregiao"]

        numColuna = int(valorMicro)

        if numColuna == alvo:
            bairro = linha["bairro"]
            if pd.notna(bairro):
                bairros.append(str(bairro))

    return bairros

def arestasAdjacentes(bairros):
    cont = 0

    conjunto = set([b.strip() for b in bairros if pd.notna(b)])

    for _, linha in dtArestas.iterrows():
        origem = str(linha["bairro_origem"])
        destino = str(linha["bairro_destino"])

        if origem in conjunto and destino in conjunto:
            cont += 1

    return cont

for i in range(1, 7):
    bairros = listarBairros(i)
    ordem = len(bairros)
    tamanho = arestasAdjacentes(bairros)
    densidade = calcularDensidade(ordem, tamanho)

    dadosMicros["microrregiao"].append(str(i))
    dadosMicros["ordem"].append(ordem)
    dadosMicros["tamanho"].append(tamanho)
    dadosMicros["densidade"].append(densidade)

dfMicros = pd.DataFrame(dadosMicros)
dfMicros.to_json("out/microrregioes.json", orient="records", indent=4, force_ascii=False)

#EGO 

dadosEgo = {
    "bairro": [],
    "grau": [],
    "ordem_ego": [],
    "tamanho_ego": [],
    "densidade_ego": []
}

def listarBairrosEgo(numero):
    bairros = []

    for _, linha in dtBairros.iterrows():
        valorMicro = linha["microrregiao"]

        if valorMicro == numero:
            bairro = linha["bairro"]
            if pd.notna(bairro):
                bairros.append(str(bairro))

    return bairros

def gerarGrauGrupo(bairros, bairro):
    cont = 0
    conjunto = set(bairros)

    for _, linha in dtArestas.iterrows():
        origem = str(linha["bairro_origem"])
        destino = str(linha["bairro_destino"])

        # se o bairro aparecer em uma das pontas da aresta
        if origem == bairro and destino in conjunto:
            cont += 1
        elif destino == bairro and origem in conjunto:
            cont += 1

    return cont



for _, linha in dtBairros.iterrows():
    bairro = str(linha["bairro"])
    micro = linha["microrregiao"]

    bairros = listarBairrosEgo(micro)

    grau = gerarGrauGrupo(bairros, bairro)

    dadosEgo["bairro"].append(bairro)
    dadosEgo["grau"].append(grau)
    dadosEgo["ordem_ego"].append(len(bairros))
    dadosEgo["tamanho_ego"].append(arestasAdjacentes(bairros))
    dadosEgo["densidade_ego"].append(calcularDensidade(len(bairros),arestasAdjacentes(bairros)))

dfEgo = pd.DataFrame(dadosEgo)
dfEgo.to_csv("out/ego_bairro.csv", index=False, encoding="utf-8")