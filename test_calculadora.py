import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import calculadora


class TestOperaciones(unittest.TestCase):
    def test_suma(self):
        self.assertEqual(calculadora.suma(2, 3), 5)
        self.assertEqual(calculadora.suma(-1, 1), 0)

    def test_resta(self):
        self.assertEqual(calculadora.resta(5, 3), 2)
        self.assertEqual(calculadora.resta(3, 5), -2)

    def test_multiplicacion(self):
        self.assertEqual(calculadora.multiplicacion(4, 3), 12)
        self.assertEqual(calculadora.multiplicacion(4, 0), 0)

    def test_division(self):
        self.assertEqual(calculadora.division(10, 2), 5)
        self.assertAlmostEqual(calculadora.division(1, 3), 0.3333333, places=6)

    def test_division_por_cero(self):
        with self.assertRaises(ZeroDivisionError):
            calculadora.division(1, 0)


class TestCLI(unittest.TestCase):
    def ejecutar(self, *args):
        salida, errores = io.StringIO(), io.StringIO()
        with redirect_stdout(salida), redirect_stderr(errores):
            codigo = calculadora.main(list(args))
        return codigo, salida.getvalue().strip(), errores.getvalue().strip()

    def test_operaciones(self):
        casos = [
            (("suma", "2", "3"), "5"),
            (("resta", "2", "3"), "-1"),
            (("multiplicacion", "2.5", "2"), "5"),
            (("division", "1", "4"), "0.25"),
        ]
        for args, esperado in casos:
            with self.subTest(args=args):
                codigo, salida, _ = self.ejecutar(*args)
                self.assertEqual(codigo, 0)
                self.assertEqual(salida, esperado)

    def test_division_por_cero(self):
        codigo, salida, errores = self.ejecutar("division", "1", "0")
        self.assertEqual(codigo, 1)
        self.assertEqual(salida, "")
        self.assertIn("dividir por cero", errores)

    def test_operacion_invalida(self):
        with self.assertRaises(SystemExit) as contexto:
            self.ejecutar("potencia", "2", "3")
        self.assertEqual(contexto.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
