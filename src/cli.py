import argparse
from .solve import calcular_distancias, gerar_grafo_interativo

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc-enderecos", action="store_true",
                        help="Calcula distancias entre enderecos e gera JSON/CSV.")
    parser.add_argument("--grafo-interativo", action="store_true",
                        help="Gera out/grafo_interativo.html com o grafo dos bairros.")

    args = parser.parse_args()

    if args.calc_enderecos:
        calcular_distancias()

    if args.grafo_interativo:
        gerar_grafo_interativo()

if __name__ == "__main__":
    main()
