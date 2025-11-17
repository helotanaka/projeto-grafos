import argparse
from .test_dijkstra import calcular_distancias

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc-enderecos-parte2", action="store_true")
    args = parser.parse_args()

    if args.calc_enderecos_parte2:
        calcular_distancias()

if __name__ == "__main__":
    main()
