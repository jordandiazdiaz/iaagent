"""Calculadora simple: suma, resta, multiplicación y división."""

import argparse
import sys


def suma(a, b):
    return a + b


def resta(a, b):
    return a - b


def multiplicacion(a, b):
    return a * b


def division(a, b):
    if b == 0:
        raise ZeroDivisionError("no se puede dividir por cero")
    return a / b


OPERACIONES = {
    "suma": suma,
    "resta": resta,
    "multiplicacion": multiplicacion,
    "division": division,
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="calculadora", description="Calculadora simple de línea de comandos."
    )
    parser.add_argument("operacion", choices=OPERACIONES, help="operación a realizar")
    parser.add_argument("a", type=float, help="primer operando")
    parser.add_argument("b", type=float, help="segundo operando")
    args = parser.parse_args(argv)

    try:
        resultado = OPERACIONES[args.operacion](args.a, args.b)
    except ZeroDivisionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # Muestra los enteros sin el ".0" final
    print(int(resultado) if resultado.is_integer() else resultado)
    return 0


if __name__ == "__main__":
    sys.exit(main())
