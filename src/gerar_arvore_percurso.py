import json
import os
import matplotlib.pyplot as plt

with open("out/percurso_nova_descoberta_setubal.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

caminho = dados["caminho"]
origem = dados["origem"]
destino = dados["destino"]

arestas = [(caminho[i], caminho[i + 1]) for i in range(len(caminho) - 1)]

posicoes = {}
for i, bairro in enumerate(caminho):
    posicoes[bairro] = (0, -i)  # x=0 fixo, y negativo para descer

# Desenho da arvore
plt.figure(figsize=(6, len(caminho) * 0.6))
ax = plt.gca()

# Arestas destacadas
for (a, b) in arestas:
    x1, y1 = posicoes[a]
    x2, y2 = posicoes[b]
    ax.plot([x1, x2], [y1, y2], color="red", linewidth=3, zorder=1)

# Nós
for bairro, (x, y) in posicoes.items():
    ax.scatter(x, y, s=200, color="orange", edgecolors="black", zorder=2)
    ax.text(x + 0.1, y, bairro.title(), va="center", fontsize=9)

# Ajustes visuais
ax.axis("off")
ax.set_title(f"Árvore de Caminho: {origem} → {destino}", fontsize=10)
plt.tight_layout()

os.makedirs("out", exist_ok=True)
plt.savefig("out/arvore_percurso.png", dpi=300, bbox_inches="tight")
plt.close()
