import argparse
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import calculadora

SCRIPT = Path(calculadora.__file__).resolve()


class TestOperaciones(unittest.TestCase):
    def test_sumar(self):
        self.assertEqual(calculadora.sumar(2, 3), 5)
        self.assertEqual(calculadora.sumar(-1, 1), 0)
        self.assertAlmostEqual(calculadora.sumar(0.1, 0.2), 0.3)

    def test_restar(self):
        self.assertEqual(calculadora.restar(5, 3), 2)
        self.assertEqual(calculadora.restar(2, -3), 5)
        self.assertAlmostEqual(calculadora.restar(0.3, 0.1), 0.2)

    def test_multiplicar(self):
        self.assertEqual(calculadora.multiplicar(4, 3), 12)
        self.assertEqual(calculadora.multiplicar(-4, 3), -12)
        self.assertAlmostEqual(calculadora.multiplicar(2.5, 0.5), 1.25)

    def test_dividir(self):
        self.assertEqual(calculadora.dividir(10, 2), 5)
        self.assertEqual(calculadora.dividir(-9, 3), -3)
        self.assertAlmostEqual(calculadora.dividir(1, 3), 0.3333333, places=6)

    def test_dividir_por_cero(self):
        with self.assertRaises(ZeroDivisionError):
            calculadora.dividir(1, 0)
        with self.assertRaises(ZeroDivisionError):
            calculadora.dividir(0, 0)

    def test_no_redondean(self):
        # El redondeo es solo de presentación: las funciones devuelven el float tal cual
        self.assertEqual(calculadora.sumar(0.1, 0.2), 0.1 + 0.2)
        self.assertNotEqual(calculadora.sumar(0.1, 0.2), 0.3)

    def test_tabla_de_operaciones(self):
        self.assertEqual(
            calculadora.OPERACIONES,
            {
                "sumar": calculadora.sumar,
                "restar": calculadora.restar,
                "multiplicar": calculadora.multiplicar,
                "dividir": calculadora.dividir,
            },
        )


class TestNumero(unittest.TestCase):
    def test_validos(self):
        casos = [
            ("2", 2.0),
            ("-3", -3.0),
            ("+4", 4.0),
            ("0.5", 0.5),
            (".5", 0.5),
            ("1e3", 1000.0),
            ("-1.5e-2", -0.015),
            (" 7 ", 7.0),
        ]
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(calculadora.numero(texto), esperado)

    def test_no_numericos(self):
        for texto in ("dos", "2,5", "", "1/2", "0x10", "2+3"):
            with self.subTest(texto=texto):
                with self.assertRaises(argparse.ArgumentTypeError):
                    calculadora.numero(texto)

    def test_no_finitos(self):
        for texto in ("nan", "inf", "-inf", "Infinity", "NaN", "1e999"):
            with self.subTest(texto=texto):
                with self.assertRaises(argparse.ArgumentTypeError):
                    calculadora.numero(texto)


class TestCLI(unittest.TestCase):
    def ejecutar(self, *args):
        salida, errores = io.StringIO(), io.StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            codigo = calculadora.main(list(args))
        return codigo, salida.getvalue().strip(), errores.getvalue().strip()

    def test_operaciones(self):
        casos = [
            (("sumar", "2", "3"), "5"),
            (("sumar", "0.1", "0.2"), "0.3"),
            (("restar", "2", "-3"), "5"),
            (("multiplicar", "2.5", "2"), "5"),
            (("dividir", "1", "4"), "0.25"),
            (("sumar", "1e3", ".5"), "1000.5"),
            (("restar", "-2", "3"), "-5"),
            (("restar", "0.3", "0.1"), "0.2"),
            (("multiplicar", "-4", "-3"), "12"),
            (("dividir", "-9", "3"), "-3"),
            (("dividir", "0", "5"), "0"),
        ]
        for args, esperado in casos:
            with self.subTest(args=args):
                codigo, salida, _ = self.ejecutar(*args)
                self.assertEqual(codigo, 0)
                self.assertEqual(salida, esperado)

    def test_formato(self):
        casos = [
            (("dividir", "1", "3"), "0.333333333333"),
            (("dividir", "2", "3"), "0.666666666667"),
            (("multiplicar", "1e10", "1e10"), "1e+20"),
            (("dividir", "1", "1e10"), "1e-10"),
            (("sumar", "123456789012", "0"), "123456789012"),
            (("sumar", "1234567890123", "0"), "1.23456789012e+12"),
        ]
        for args, esperado in casos:
            with self.subTest(args=args):
                codigo, salida, _ = self.ejecutar(*args)
                self.assertEqual(codigo, 0)
                self.assertEqual(salida, esperado)

    def test_exito_no_escribe_en_stderr(self):
        codigo, _, errores = self.ejecutar("sumar", "2", "3")
        self.assertEqual(codigo, 0)
        self.assertEqual(errores, "")

    def test_division_por_cero(self):
        casos = [("dividir", "1", "0"), ("dividir", "0", "0"), ("dividir", "1", "-0")]
        for args in casos:
            with self.subTest(args=args):
                codigo, salida, errores = self.ejecutar(*args)
                self.assertEqual(codigo, 1)
                self.assertEqual(salida, "")
                self.assertEqual(errores, "Error: división por cero")

    def test_desbordamiento(self):
        casos = [
            ("multiplicar", "1e308", "10"),
            ("multiplicar", "-1e308", "10"),
            ("sumar", "1e308", "1e308"),
            ("restar", "-1e308", "1e308"),
            ("dividir", "1e308", "1e-10"),
        ]
        for args in casos:
            with self.subTest(args=args):
                codigo, salida, errores = self.ejecutar(*args)
                self.assertEqual(codigo, 1)
                self.assertEqual(salida, "")
                self.assertEqual(errores, "Error: resultado fuera de rango")

    def test_argv_por_defecto(self):
        with mock.patch.object(sys, "argv", ["calculadora.py", "sumar", "2", "3"]):
            salida = io.StringIO()
            with redirect_stdout(salida):
                codigo = calculadora.main()
        self.assertEqual(codigo, 0)
        self.assertEqual(salida.getvalue().strip(), "5")

    def test_uso_incorrecto(self):
        casos = [
            ("potencia", "2", "3"),
            ("sumar", "dos", "3"),
            ("sumar", "2,5", "3"),
            ("sumar", "nan", "3"),
            ("sumar", "inf", "3"),
            ("sumar", "-inf", "3"),
            ("sumar", "2", "nan"),
            ("sumar", "2"),
            ("sumar",),
            (),
            ("sumar", "2", "3", "4"),
            ("SUMAR", "2", "3"),
            ("2", "sumar", "3"),
        ]
        for args in casos:
            with self.subTest(args=args):
                with self.assertRaises(SystemExit) as contexto:
                    self.ejecutar(*args)
                self.assertEqual(contexto.exception.code, 2)

    def test_uso_incorrecto_no_escribe_en_stdout(self):
        salida, errores = io.StringIO(), io.StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            with self.assertRaises(SystemExit):
                calculadora.main(["sumar", "dos", "3"])
        self.assertEqual(salida.getvalue(), "")
        self.assertNotEqual(errores.getvalue(), "")

    def test_ayuda(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            with self.assertRaises(SystemExit) as contexto:
                calculadora.main(["--help"])
        self.assertEqual(contexto.exception.code, 0)
        for nombre in calculadora.OPERACIONES:
            self.assertIn(nombre, salida.getvalue())


class TestScript(unittest.TestCase):
    """Integración: el script ejecutado como proceso, igual que desde el shell."""

    def ejecutar(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={"PYTHONIOENCODING": "utf-8"},
            timeout=30,
        )

    def test_ejemplos_del_readme(self):
        casos = [
            (("sumar", "2", "3"), "5\n"),
            (("restar", "2", "-3"), "5\n"),
            (("multiplicar", "2", "3"), "6\n"),
            (("dividir", "1", "4"), "0.25\n"),
        ]
        for args, esperado in casos:
            with self.subTest(args=args):
                proceso = self.ejecutar(*args)
                self.assertEqual(proceso.returncode, 0)
                self.assertEqual(proceso.stdout, esperado)
                self.assertEqual(proceso.stderr, "")

    def test_division_por_cero(self):
        proceso = self.ejecutar("dividir", "1", "0")
        self.assertEqual(proceso.returncode, 1)
        self.assertEqual(proceso.stdout, "")
        self.assertEqual(proceso.stderr, "Error: división por cero\n")
        self.assertNotIn("Traceback", proceso.stderr)

    def test_desbordamiento(self):
        proceso = self.ejecutar("multiplicar", "1e308", "10")
        self.assertEqual(proceso.returncode, 1)
        self.assertEqual(proceso.stdout, "")
        self.assertEqual(proceso.stderr, "Error: resultado fuera de rango\n")

    def test_uso_incorrecto(self):
        for args in (("potencia", "2", "3"), ("sumar", "dos", "3"), ("sumar", "2")):
            with self.subTest(args=args):
                proceso = self.ejecutar(*args)
                self.assertEqual(proceso.returncode, 2)
                self.assertEqual(proceso.stdout, "")
                self.assertNotEqual(proceso.stderr, "")
                self.assertNotIn("Traceback", proceso.stderr)


if __name__ == "__main__":
    unittest.main()
