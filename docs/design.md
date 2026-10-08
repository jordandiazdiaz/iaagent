# Diseño: calculadora en Python

Bead: `ia-wfs-hg3je` (diseño). Lo implementa `ia-wfs-6l6nc`.

## Alcance

Una calculadora de línea de comandos con cuatro operaciones binarias: suma,
resta, multiplicación y división, más tests unitarios.

Fuera de alcance: expresiones (`2 + 3 * 4`), paréntesis, modo interactivo,
más operaciones, empaquetado (`pyproject.toml`, entry points) y cualquier
dependencia externa.

## Encaje en el sistema

El repositorio solo contiene `README.md`, así que no hay convenciones previas
que respetar. El host tiene Python 3.14 y **no** tiene `pytest`; los polecats
no pueden instalar paquetes. Por eso todo usa la biblioteca estándar:
`argparse` para el CLI y `unittest` para los tests.

## Estructura

Dos archivos en la raíz del repositorio:

```
calculadora.py        # operaciones + CLI
test_calculadora.py   # tests unitarios
```

Con cuatro funciones de una línea, un paquete con submódulos sería pura
ceremonia. La separación entre lógica y CLI se mantiene dentro del módulo:
las operaciones son funciones puras que no imprimen ni leen nada, y `main`
es la única parte que toca `argv`, stdout y stderr.

## `calculadora.py`

### Operaciones

```python
def sumar(a: float, b: float) -> float
def restar(a: float, b: float) -> float
def multiplicar(a: float, b: float) -> float
def dividir(a: float, b: float) -> float   # lanza ZeroDivisionError si b == 0

OPERACIONES = {"sumar": sumar, "restar": restar,
               "multiplicar": multiplicar, "dividir": dividir}
```

- `dividir` deja propagar el `ZeroDivisionError` nativo de Python. No se
  define una excepción propia ni se devuelve `None`/`inf`.
- `OPERACIONES` es la única fuente de verdad: el CLI saca de ahí los nombres
  válidos y la función a llamar. Añadir una operación es añadir una entrada.

### CLI

```
python3 calculadora.py <operacion> <a> <b>

python3 calculadora.py sumar 2 3        -> 5
python3 calculadora.py dividir 1 4      -> 0.25
python3 calculadora.py restar 2 -3      -> 5
```

- `operacion`: posicional con `choices=OPERACIONES`.
- `a`, `b`: posicionales con un `type` propio (`numero`) que convierte con
  `float()` y rechaza valores no finitos con `argparse.ArgumentTypeError`.
- Firma: `main(argv: list[str] | None = None) -> int`. Devuelve el código de
  salida en vez de llamar a `sys.exit`, para poder testearla sin subprocesos.
  El bloque `if __name__ == "__main__":` hace `raise SystemExit(main())`.

Se usan nombres de operación en vez de símbolos (`2 * 3`) porque el shell
expande `*` como glob y obligaría a entrecomillarlo.

### Salida y códigos de retorno

| Caso | stdout | stderr | Código |
|------|--------|--------|--------|
| Éxito | resultado | — | 0 |
| División por cero | — | `Error: división por cero` | 1 |
| Resultado no finito (desbordamiento) | — | `Error: resultado fuera de rango` | 1 |
| Uso incorrecto (operación desconocida, argumento no numérico, faltan argumentos) | — | mensaje de `argparse` | 2 |

El resultado se imprime con `format(resultado, ".12g")`. Eso resuelve dos
cosas a la vez: los enteros salen sin `.0` (`5`, no `5.0`) y el ruido de coma
flotante desaparece (`0.1 + 0.2` imprime `0.3`, no `0.30000000000000004`). El
redondeo vive solo en la presentación; las funciones devuelven el `float` sin
tocar.

## Casos límite

| Caso | Comportamiento |
|------|----------------|
| `dividir 1 0` | Código 1, mensaje en stderr, sin traceback. |
| `dividir 0 0` | Igual que el anterior (Python lanza `ZeroDivisionError`). |
| Segundo operando negativo (`restar 2 -3`) | Funciona: `argparse` trata `-3` como número porque el parser no define opciones con forma de número negativo. Hay que cubrirlo con un test para que no se rompa si alguien añade flags. |
| `nan`, `inf`, `-inf` como entrada | `float()` los acepta; `numero` los rechaza (código 2). |
| Desbordamiento (`multiplicar 1e308 10`) | El producto de floats da `inf` sin lanzar excepción; `main` lo comprueba con `math.isfinite` y devuelve 1. |
| Notación científica y decimales (`1e3`, `.5`) | Aceptados tal cual por `float()`. |
| Coma decimal (`2,5`) | Rechazado (código 2). No se intenta adivinar la configuración regional. |
| Resultados muy grandes o muy pequeños | `.12g` cambia a notación científica (`1e+15`). Aceptable. |
| Más de 12 cifras significativas | Se redondean al imprimir. Aceptable para esta herramienta. |

## Qué puede salir mal

- **Precisión.** `float` no es exacto. Para una calculadora de cuatro
  operaciones basta con redondear al mostrar. Si algún día hiciera falta
  aritmética decimal exacta, el cambio queda acotado a `numero` y al formato.
- **Mensajes de `argparse` en inglés.** Los errores de uso salen con el texto
  estándar de `argparse`. No se traducen: no compensa el código adicional.
- **Tests frágiles.** Los tests del CLI comprueban código de retorno y stdout,
  no el texto exacto de los errores de `argparse`, que cambia entre versiones
  de Python.

## Tests (`test_calculadora.py`)

Con `unittest`. Se ejecutan desde la raíz con:

```
python3 -m unittest
```

Operaciones:

- Cada operación con enteros, decimales y negativos.
- `dividir` con divisor cero lanza `ZeroDivisionError`.
- Comparaciones de decimales con `assertAlmostEqual`.

CLI, llamando a `main([...])` y capturando la salida con
`contextlib.redirect_stdout` / `redirect_stderr`:

- Cada operación devuelve 0 e imprime el resultado esperado.
- Formato: `sumar 2 3` imprime `5`; `sumar 0.1 0.2` imprime `0.3`.
- `restar 2 -3` imprime `5`.
- `dividir 1 0` devuelve 1, stdout vacío, stderr no vacío.
- `multiplicar 1e308 10` devuelve 1.
- Operación desconocida, argumento no numérico, `nan` y argumentos de menos
  terminan con `SystemExit` de código 2 (`argparse` sale por su cuenta en
  errores de uso).

## Alternativas descartadas

- **Paquete `calculadora/` con `operaciones.py`, `cli.py`, `__main__.py`.**
  Más archivos sin ningún beneficio a este tamaño.
- **`decimal.Decimal`.** Exacto, pero trae sus propias rarezas (contexto,
  `InvalidOperation` para `0/0`, 28 dígitos en `1/3`) y no hace falta.
- **Sintaxis infija (`calculadora.py 2 + 3`).** Más natural, pero `*` choca
  con el shell.
- **`pytest`.** No está instalado y no se puede instalar.
