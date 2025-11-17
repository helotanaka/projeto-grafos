import argparse
from .solve import calcular_distancias
from .solve_dijkstra_parte2 import calcular_distancias as calcular_distancias_parte2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc-enderecos", action="store_true")
    args = parser.parse_args()

    if args.calc_enderecos:
        calcular_distancias()
        calcular_distancias_parte2()

if __name__ == "__main__":
    main()
