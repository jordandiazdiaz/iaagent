import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import calculadora


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
        ]
        for args, esperado in casos:
            with self.subTest(args=args):
                codigo, salida, _ = self.ejecutar(*args)
                self.assertEqual(codigo, 0)
                self.assertEqual(salida, esperado)

    def test_division_por_cero(self):
        for args in (("dividir", "1", "0"), ("dividir", "0", "0")):
            with self.subTest(args=args):
                codigo, salida, errores = self.ejecutar(*args)
                self.assertEqual(codigo, 1)
                self.assertEqual(salida, "")
                self.assertNotEqual(errores, "")

    def test_desbordamiento(self):
        codigo, salida, errores = self.ejecutar("multiplicar", "1e308", "10")
        self.assertEqual(codigo, 1)
        self.assertEqual(salida, "")
        self.assertNotEqual(errores, "")

    def test_uso_incorrecto(self):
        casos = [
            ("potencia", "2", "3"),
            ("sumar", "dos", "3"),
            ("sumar", "2,5", "3"),
            ("sumar", "nan", "3"),
            ("sumar", "inf", "3"),
            ("sumar", "2"),
        ]
        for args in casos:
            with self.subTest(args=args):
                with self.assertRaises(SystemExit) as contexto:
                    self.ejecutar(*args)
                self.assertEqual(contexto.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
