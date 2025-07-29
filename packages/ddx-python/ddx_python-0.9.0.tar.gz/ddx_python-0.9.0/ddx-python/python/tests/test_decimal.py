import copy
import csv
import unittest
from decimal import Decimal as PyDecimal
from decimal import localcontext
from os import listdir, path

from ddx._rust.decimal import Decimal, DecimalError


class DecimalTests(unittest.TestCase):
    tests_dir = "python/tests/decimal"

    def test_examples_from_issue(self):
        # the specific examples from Adi's issue for sanity
        # Rust versions
        self.assertEqual(
            Decimal("5631989.747461568422879160")
            + Decimal("12354.867325583148587639999525"),
            Decimal("5644344.6147871515714667999995"),
        )
        self.assertEqual(
            Decimal("6631989.747461568422879160")
            + Decimal("12354.867325583148587639999525"),
            Decimal("6644344.6147871515714667999995"),
        )
        self.assertEqual(
            Decimal("7631989.747461568422879160")
            + Decimal("12354.867325583148587639999525"),
            Decimal("7644344.6147871515714667999995"),
        )
        self.assertEqual(
            Decimal("8631989.747461568422879160")
            + Decimal("12354.867325583148587639999525"),
            Decimal("8644344.6147871515714668000000"),
        )

        # Python versions with specified context
        with localcontext() as ctx:
            ctx.prec = 29
            ctx.Emin = 0
            ctx.Emax = 28
            ctx.clamp = 1
            self.assertEqual(
                PyDecimal("5631989.747461568422879160")
                + PyDecimal("12354.867325583148587639999525"),
                PyDecimal("5644344.6147871515714667999995"),
            )
            self.assertEqual(
                PyDecimal("6631989.747461568422879160")
                + PyDecimal("12354.867325583148587639999525"),
                PyDecimal("6644344.6147871515714667999995"),
            )
            self.assertEqual(
                PyDecimal("7631989.747461568422879160")
                + PyDecimal("12354.867325583148587639999525"),
                PyDecimal("7644344.6147871515714667999995"),
            )
            self.assertEqual(
                PyDecimal("8631989.747461568422879160")
                + PyDecimal("12354.867325583148587639999525"),
                PyDecimal("8644344.6147871515714667999995"),
            )

    def test_comparisons(self):
        d1 = Decimal("-1234.5678")
        d2 = Decimal("8765.4321")
        self.assertTrue(d1 < d2)
        self.assertTrue(d2 > d1)
        self.assertTrue(d2 != d1)
        self.assertTrue(d1 <= d2)
        self.assertTrue(d2 >= d1)
        d3 = Decimal("-1234.5678")
        self.assertTrue(d1 == d3)
        self.assertTrue(d1 <= d3)

    def test_hash(self):
        v1 = Decimal("3458.20")
        v2 = Decimal("3458.2")
        v3 = Decimal("3458.21")
        self.assertEqual(v1, v2)
        self.assertEqual(hash(v1), hash(v2))
        self.assertNotEqual(v1, v3)
        self.assertNotEqual(hash(v1), hash(v3))
        d = {v1: 3}
        self.assertIn(v2, d)
        self.assertNotIn(v3, d)

    def test_int_casting(self):
        values = [
            (Decimal("6.5"), PyDecimal("6.5")),
            (Decimal("7.5"), PyDecimal("7.5")),
            (Decimal("6.7"), PyDecimal("6.7")),
            (Decimal("7.7"), PyDecimal("7.7")),
            (Decimal("6.1"), PyDecimal("6.1")),
            (Decimal("7.1"), PyDecimal("7.1")),
        ]
        for v, py_v in values:
            self.assertEqual(int(v), int(py_v))
            self.assertEqual(int(-v), int(-py_v))

    def test_float_casting(self):
        self.assertEqual(float(Decimal("1.123")), 1.123)
        self.assertEqual(float(Decimal("-1.123")), -1.123)
        self.assertEqual(float(Decimal("1")), 1.0)

    def test_int_arithemtic(self):
        self.assertEqual(Decimal("5") + 1, Decimal("6"))
        self.assertEqual(1 + Decimal("5"), Decimal("6"))

        self.assertEqual(Decimal("5") - 1, Decimal("4"))
        self.assertEqual(5 - Decimal("1"), Decimal("4"))

        self.assertEqual(Decimal("5") * 2, Decimal("10"))
        self.assertEqual(2 * Decimal("5"), Decimal("10"))

        self.assertEqual(Decimal("5") / 2, Decimal("2.5"))
        self.assertEqual(12 / Decimal("4"), Decimal("3"))

    def test_float_arithemtic(self):
        self.assertEqual(Decimal("5") + 1.1, Decimal("6.1"))
        self.assertEqual(1.1 + Decimal("5"), Decimal("6.1"))

        self.assertEqual(Decimal("5") - 1.1, Decimal("3.9"))
        self.assertEqual(4.9 - Decimal("1"), Decimal("3.9"))

        self.assertEqual(Decimal("5") * 2.5, Decimal("12.5"))
        self.assertEqual(2.5 * Decimal("5"), Decimal("12.5"))

        self.assertEqual(Decimal("5") / 2.5, Decimal("2"))
        self.assertEqual(12.5 / Decimal("4"), Decimal("3.125"))

    def test_ipow(self):
        self.assertEqual(Decimal(2) ** 2, 4)
        self.assertEqual(Decimal(4) ** 3, 64)

    def test_copy(self):
        temp = {"a": Decimal("5"), "b": Decimal("10")}
        temp2 = copy.deepcopy(temp)
        self.assertEqual(temp, temp2)

    def test_sci_notation(self):
        self.assertEqual(int(Decimal("1e18")), int(PyDecimal("1e18")))
        self.assertEqual(float(Decimal("123456e3")), float(PyDecimal("123456e3")))

    def get_test_csv_row_values(self, row: dict) -> (Decimal, Decimal, Decimal, str):
        return (
            Decimal(row["D1"]),
            Decimal(row["D2"]),
            Decimal(row["Result"]),
            row["Error"],
        )

    def get_test_csvs(self, op_name: str) -> list:
        return list(
            filter(lambda filename: op_name in filename, listdir(self.tests_dir))
        )

    def decimal_op_test(self, f, op_name: str):
        test_csvs = self.get_test_csvs(op_name)
        for test_csv in test_csvs:
            with open(path.join(self.tests_dir, test_csv)) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    d1, d2, result, err = self.get_test_csv_row_values(row)
                    if err:
                        with self.assertRaises(DecimalError):
                            f(d1, d2)
                    else:
                        self.assertEqual(f(d1, d2), result)

    def test_add(self):
        self.decimal_op_test(lambda x, y: x + y, "Add")

    def test_sub(self):
        self.decimal_op_test(lambda x, y: x - y, "Sub")

    def test_mul(self):
        self.decimal_op_test(lambda x, y: x * y, "Mul")

    def test_div(self):
        self.decimal_op_test(lambda x, y: x / y, "Div")

    def test_rem(self):
        self.decimal_op_test(lambda x, y: x % y, "Rem")


if __name__ == "__main__":
    unittest.main()
