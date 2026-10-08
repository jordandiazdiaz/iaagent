"""Calculadora simple: suma, resta, multiplicación y división."""

import argparse
import math
import sys


def sumar(a: float, b: float) -> float:
    return a + b


def restar(a: float, b: float) -> float:
    return a - b


def multiplicar(a: float, b: float) -> float:
    return a * b


def dividir(a: float, b: float) -> float:
    return a / b


OPERACIONES = {
    "sumar": sumar,
    "restar": restar,
    "multiplicar": multiplicar,
    "dividir": dividir,
}


def numero(texto: str) -> float:
    try:
        valor = float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"número no válido: {texto!r}")
    if not math.isfinite(valor):
        raise argparse.ArgumentTypeError(f"número no finito: {texto!r}")
    return valor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="calculadora", description="Calculadora simple de línea de comandos."
    )
    parser.add_argument("operacion", choices=OPERACIONES, help="operación a realizar")
    parser.add_argument("a", type=numero, help="primer operando")
    parser.add_argument("b", type=numero, help="segundo operando")
    args = parser.parse_args(argv)

    try:
        resultado = OPERACIONES[args.operacion](args.a, args.b)
    except ZeroDivisionError:
        print("Error: división por cero", file=sys.stderr)
        return 1

    if not math.isfinite(resultado):
        print("Error: resultado fuera de rango", file=sys.stderr)
        return 1

    # El redondeo vive solo en la presentación: sin ".0" ni ruido de coma flotante
    print(format(resultado, ".12g"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
