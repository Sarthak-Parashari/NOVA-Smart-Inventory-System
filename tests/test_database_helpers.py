import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

import database


class DatabaseValidationTests(unittest.TestCase):
    def test_positive_integer_rejects_zero(self):
        with self.assertRaises(ValueError):
            database._positive_integer(0, "Product ID")

    def test_positive_integer_rejects_bool(self):
        with self.assertRaises(ValueError):
            database._positive_integer(True, "Product ID")

    def test_non_negative_integer_accepts_zero(self):
        self.assertEqual(database._non_negative_integer(0, "Stock quantity"), 0)

    def test_non_negative_price_accepts_decimal(self):
        self.assertEqual(
            database._non_negative_price("12.50", "Purchase price"),
            Decimal("12.50"),
        )

    def test_non_negative_price_rejects_negative(self):
        with self.assertRaises(ValueError):
            database._non_negative_price(-1, "Purchase price")

    @patch("database.mysql.connector.connect")
    def test_get_connection_requires_password(self, mock_connect):
        os.environ.pop("SMART_INVENTORY_DB_PASSWORD", None)
        with self.assertRaises(RuntimeError):
            database.get_connection()
        mock_connect.assert_not_called()

    @patch("database.mysql.connector.connect")
    def test_get_connection_uses_environment_overrides(self, mock_connect):
        os.environ["SMART_INVENTORY_DB_PASSWORD"] = "secret"
        os.environ["SMART_INVENTORY_DB_HOST"] = "localhost"
        os.environ["SMART_INVENTORY_DB_USER"] = "app_user"
        os.environ["SMART_INVENTORY_DB_NAME"] = "smart_inventory"
        os.environ["SMART_INVENTORY_DB_PORT"] = "3307"

        database.get_connection()

        mock_connect.assert_called_once_with(
            host="localhost",
            user="app_user",
            password="secret",
            database="smart_inventory",
            connection_timeout=5,
            port=3307,
        )

    @patch("database.get_connection")
    def test_add_product_inserts_expected_values(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_get_connection.return_value = mock_connection

        mock_connection.cursor.return_value = mock_cursor
        mock_connection.start_transaction = MagicMock()

        result = database.add_product(
            "Laptop",
            "Electronics",
            200.0,
            350.0,
            8,
            5,
        )

        self.assertEqual(result, 42)
        mock_cursor.execute.assert_any_call(
            """
            INSERT INTO Products
            (product_name, category, purchase_price,
             selling_price, stock_quantity, reorder_level)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                "Laptop",
                "Electronics",
                Decimal("200.0"),
                Decimal("350.0"),
                8,
                5,
            ),
        )

    @patch("database.get_connection")
    def test_record_sale_rejects_insufficient_stock(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Laptop", 2, 10.0, 5.0)
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.start_transaction = MagicMock()

        with self.assertRaises(database.InsufficientStockError):
            database.record_sale(1, 3, "Customer A")

    def tearDown(self):
        os.environ.pop("SMART_INVENTORY_DB_PASSWORD", None)
        os.environ.pop("SMART_INVENTORY_DB_HOST", None)
        os.environ.pop("SMART_INVENTORY_DB_USER", None)
        os.environ.pop("SMART_INVENTORY_DB_NAME", None)
        os.environ.pop("SMART_INVENTORY_DB_PORT", None)


if __name__ == "__main__":
    unittest.main()
