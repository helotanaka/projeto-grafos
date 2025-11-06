from collections import defaultdict
from typing import Dict, List, Tuple

class Graph:
    def __init__(self):
        # usar dict para evita duplicar arestas e facilita manter o menor peso
        self.adj: Dict[str, Dict[str, float]] = defaultdict(dict)

    def adicionar_no(self, no: str) -> None:
        _ = self.adj[no]  # força criação

    def adicionar_aresta(self, origem: str, destino: str, peso: float) -> None:
        # origem -> destino
        if destino in self.adj[origem]:
            self.adj[origem][destino] = min(self.adj[origem][destino], peso)
        else:
            self.adj[origem][destino] = peso

        # destino -> origem (espelho)
        if origem in self.adj[destino]:
            self.adj[destino][origem] = min(self.adj[destino][origem], peso)
        else:
            self.adj[destino][origem] = peso

    def vizinhos(self, no: str) -> List[Tuple[str, float]]:
        return list(self.adj[no].items())

    def nos(self) -> List[str]:
        return list(self.adj.keys())

    def tem_no(self, no: str) -> bool:
        return no in self.adj

    def ordem(self) -> int:
        return len(self.adj)

    def tamanho(self) -> int:
        # cada aresta aparece duas vezes, então divide por 2
        return sum(len(vs) for vs in self.adj.values()) // 2

    def grau(self, no: str) -> int:
        return len(self.adj[no])

    def possui_peso_negativo(self) -> bool:
        for u, vs in self.adj.items():
            for v, w in vs.items():
                if w < 0:
                    return True
        return False

    @classmethod
    def from_arestas(cls, arestas: List[Tuple[str, str, float]]):
        g = cls()
        for u, v, w in arestas:
            g.adicionar_aresta(u, v, w)
        return g
