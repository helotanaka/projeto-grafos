import argparse
from .test_dijkstra import calcular_distancias as calcular_dijkstra
from .test_bellman_ford import calcular_distancias_bellman_ford as calcular_bellmanford

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc-enderecos-parte2", action="store_true")
    args = parser.parse_args()

    if args.calc_enderecos_parte2:
        calcular_dijkstra()
        calcular_bellmanford()

if __name__ == "__main__":
    main()
