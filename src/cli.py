import argparse
from .solve import calcular_distancias

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc-enderecos", action="store_true")
    args = parser.parse_args()

    if args.calc_enderecos:
        calcular_distancias()

if __name__ == "__main__":
    main()
