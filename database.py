"""Reusable MySQL operations for the existing smart_inventory database."""

import os
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation

import mysql.connector


DATABASE_NAME = "smart_inventory"
DEFAULT_REORDER_LEVEL = 10


class DatabaseOperationError(Exception):
    """Base exception for expected database-layer operation failures."""


class ProductNotFoundError(DatabaseOperationError):
    """Raised when an operation refers to a product that does not exist."""


class InsufficientStockError(DatabaseOperationError):
    """Raised when a requested sale quantity exceeds available stock."""


def get_connection():
    """Open one connection using environment-configured credentials.

    SMART_INVENTORY_DB_PASSWORD is required. Host, user, port, and database
    default to localhost, root, 3306, and smart_inventory respectively.
    Connector errors are intentionally allowed to propagate to the caller.
    """
    password = os.environ.get("SMART_INVENTORY_DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "Database password is not configured. Set "
            "SMART_INVENTORY_DB_PASSWORD before starting the application."
        )

    settings = {
        "host": os.environ.get("SMART_INVENTORY_DB_HOST", "localhost"),
        "user": os.environ.get("SMART_INVENTORY_DB_USER", "root"),
        "password": password,
        "database": os.environ.get("SMART_INVENTORY_DB_NAME", DATABASE_NAME),
        "connection_timeout": 5,
    }
    port = os.environ.get("SMART_INVENTORY_DB_PORT")
    if port:
        try:
            settings["port"] = int(port)
        except ValueError as error:
            raise RuntimeError(
                "SMART_INVENTORY_DB_PORT must be a valid integer."
            ) from error

    return mysql.connector.connect(**settings)


@contextmanager
def _database_cursor(transaction=False):
    """Yield a connection and cursor and reliably close both resources."""
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if transaction:
            connection.start_transaction()
        cursor = connection.cursor()
        yield connection, cursor
    except BaseException:
        if transaction and connection is not None:
            connection.rollback()
        raise
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if connection is not None:
                connection.close()


def _positive_integer(value, field_name):
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{field_name} must be a positive integer.") from error
    if parsed <= 0 or (not isinstance(value, str) and value != parsed):
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed


def _non_negative_integer(value, field_name):
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            f"{field_name} must be a non-negative integer."
        ) from error
    if parsed < 0 or (not isinstance(value, str) and value != parsed):
        raise ValueError(f"{field_name} must be a non-negative integer.")
    return parsed


def _non_negative_price(value, field_name):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a valid number.") from error
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field_name} must be a finite, non-negative number.")
    return parsed


def get_all_products():
    """Return products as tuples ordered by product_id.

    Tuple order matches the existing product Treeview:
    product_id, product_name, category, purchase_price, selling_price,
    stock_quantity, reorder_level.
    """
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT product_id, product_name, category,
                   purchase_price, selling_price,
                   stock_quantity, reorder_level
            FROM Products
            ORDER BY product_id
        """)
        return cursor.fetchall()


def search_products(keyword):
    """Search product_name and category using a parameterized LIKE query."""
    keyword = str(keyword or "").strip()
    if not keyword:
        return get_all_products()

    pattern = f"%{keyword}%"
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT product_id, product_name, category,
                   purchase_price, selling_price,
                   stock_quantity, reorder_level
            FROM Products
            WHERE product_name LIKE %s
               OR COALESCE(category, '') LIKE %s
            ORDER BY product_id
        """, (pattern, pattern))
        return cursor.fetchall()


def get_product_by_id(product_id):
    """Return a product tuple in get_all_products order, or None if absent."""
    product_id = _positive_integer(product_id, "Product ID")
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT product_id, product_name, category,
                   purchase_price, selling_price,
                   stock_quantity, reorder_level
            FROM Products
            WHERE product_id = %s
        """, (product_id,))
        return cursor.fetchone()


def add_product(
    product_name,
    category,
    purchase_price,
    selling_price,
    stock_quantity,
    reorder_level=DEFAULT_REORDER_LEVEL,
):
    """Insert a product and return its generated product_id."""
    product_name = str(product_name or "").strip()
    if not product_name:
        raise ValueError("Product name is required.")
    purchase_price = _non_negative_price(purchase_price, "Purchase price")
    selling_price = _non_negative_price(selling_price, "Selling price")
    stock_quantity = _non_negative_integer(stock_quantity, "Stock quantity")
    reorder_level = _non_negative_integer(reorder_level, "Reorder level")
    category = str(category).strip() if category is not None else ""

    with _database_cursor(transaction=True) as (connection, cursor):
        cursor.execute("""
            INSERT INTO Products
            (product_name, category, purchase_price,
             selling_price, stock_quantity, reorder_level)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            product_name,
            category or None,
            purchase_price,
            selling_price,
            stock_quantity,
            reorder_level,
        ))
        product_id = cursor.lastrowid
        connection.commit()
        return product_id


def update_product(
    product_id,
    product_name,
    category,
    purchase_price,
    selling_price,
    stock_quantity,
    reorder_level=DEFAULT_REORDER_LEVEL,
):
    """Update an existing product; raise ProductNotFoundError if absent."""
    product_id = _positive_integer(product_id, "Product ID")
    product_name = str(product_name or "").strip()
    if not product_name:
        raise ValueError("Product name is required.")
    purchase_price = _non_negative_price(purchase_price, "Purchase price")
    selling_price = _non_negative_price(selling_price, "Selling price")
    stock_quantity = _non_negative_integer(stock_quantity, "Stock quantity")
    reorder_level = _non_negative_integer(reorder_level, "Reorder level")
    category = str(category).strip() if category is not None else ""

    with _database_cursor(transaction=True) as (connection, cursor):
        cursor.execute(
            "SELECT product_id FROM Products WHERE product_id = %s FOR UPDATE",
            (product_id,),
        )
        if cursor.fetchone() is None:
            raise ProductNotFoundError(f"Product ID {product_id} was not found.")

        cursor.execute("""
            UPDATE Products
            SET product_name = %s,
                category = %s,
                purchase_price = %s,
                selling_price = %s,
                stock_quantity = %s,
                reorder_level = %s
            WHERE product_id = %s
        """, (
            product_name,
            category or None,
            purchase_price,
            selling_price,
            stock_quantity,
            reorder_level,
            product_id,
        ))
        connection.commit()
        return True


def delete_product(product_id):
    """Delete a product; foreign-key failures propagate from MySQL."""
    product_id = _positive_integer(product_id, "Product ID")
    with _database_cursor(transaction=True) as (connection, cursor):
        cursor.execute(
            "DELETE FROM Products WHERE product_id = %s",
            (product_id,),
        )
        if cursor.rowcount == 0:
            raise ProductNotFoundError(f"Product ID {product_id} was not found.")
        connection.commit()
        return True


def get_total_product_count():
    with _database_cursor() as (_, cursor):
        cursor.execute("SELECT COUNT(*) AS total_products FROM Products")
        return cursor.fetchone()[0] or 0


def get_total_stock_units():
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT COALESCE(SUM(stock_quantity), 0) AS total_stock_units
            FROM Products
        """)
        return cursor.fetchone()[0] or 0


def get_low_stock_products(limit=None):
    """Return (product_name, category, stock_quantity, reorder_level) tuples."""
    query = """
        SELECT product_name, category,
               COALESCE(stock_quantity, 0) AS stock_quantity,
               COALESCE(reorder_level, %s) AS reorder_level
        FROM Products
        WHERE COALESCE(stock_quantity, 0)
              <= COALESCE(reorder_level, %s)
        ORDER BY stock_quantity, product_name
    """
    parameters = [DEFAULT_REORDER_LEVEL, DEFAULT_REORDER_LEVEL]
    if limit is not None:
        limit = _positive_integer(limit, "Limit")
        query += " LIMIT %s"
        parameters.append(limit)

    with _database_cursor() as (_, cursor):
        cursor.execute(query, tuple(parameters))
        return cursor.fetchall()


def get_low_stock_product_count():
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT COUNT(*) AS low_stock_product_count
            FROM Products
            WHERE COALESCE(stock_quantity, 0)
                  <= COALESCE(reorder_level, %s)
        """, (DEFAULT_REORDER_LEVEL,))
        return cursor.fetchone()[0] or 0


def get_total_sales_transactions():
    with _database_cursor() as (_, cursor):
        cursor.execute("SELECT COUNT(*) AS total_transactions FROM Sales")
        return cursor.fetchone()[0] or 0


def get_sales_totals():
    """Return total revenue and estimated gross profit from Sale_Items."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(quantity * selling_price),
                    0
                ) AS total_revenue,
                COALESCE(
                    SUM(quantity * (selling_price - purchase_price)),
                    0
                ) AS estimated_gross_profit
            FROM Sale_Items
        """)
        revenue, estimated_gross_profit = cursor.fetchone()
        return {
            "total_revenue": revenue or 0,
            "estimated_gross_profit": estimated_gross_profit or 0,
        }


def get_total_revenue():
    return get_sales_totals()["total_revenue"]


def get_estimated_gross_profit():
    return get_sales_totals()["estimated_gross_profit"]


def get_dashboard_metrics():
    """Return all six KPI values with stable, descriptive dictionary keys."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM Products) AS total_products,
                (
                    SELECT COALESCE(SUM(stock_quantity), 0)
                    FROM Products
                ) AS total_stock_units,
                (SELECT COUNT(*) FROM Sales) AS total_sales_transactions,
                (
                    SELECT COALESCE(SUM(quantity * selling_price), 0)
                    FROM Sale_Items
                ) AS total_revenue,
                (
                    SELECT COALESCE(
                        SUM(quantity * (selling_price - purchase_price)),
                        0
                    )
                    FROM Sale_Items
                ) AS estimated_gross_profit,
                (
                    SELECT COUNT(*)
                    FROM Products
                    WHERE COALESCE(stock_quantity, 0)
                          <= COALESCE(reorder_level, %s)
                ) AS low_stock_product_count
        """, (DEFAULT_REORDER_LEVEL,))
        row = cursor.fetchone()

    return {
        "total_products": row[0] or 0,
        "total_stock_units": row[1] or 0,
        "total_sales_transactions": row[2] or 0,
        "total_revenue": row[3] or 0,
        "estimated_gross_profit": row[4] or 0,
        "low_stock_product_count": row[5] or 0,
    }


def get_dashboard_data():
    """Fetch KPI metrics and low-stock rows using one database connection."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM Products) AS total_products,
                (
                    SELECT COALESCE(SUM(stock_quantity), 0)
                    FROM Products
                ) AS total_stock_units,
                (SELECT COUNT(*) FROM Sales) AS total_sales_transactions,
                (
                    SELECT COALESCE(SUM(quantity * selling_price), 0)
                    FROM Sale_Items
                ) AS total_revenue,
                (
                    SELECT COALESCE(
                        SUM(quantity * (selling_price - purchase_price)),
                        0
                    )
                    FROM Sale_Items
                ) AS estimated_gross_profit,
                (
                    SELECT COUNT(*)
                    FROM Products
                    WHERE COALESCE(stock_quantity, 0)
                          <= COALESCE(reorder_level, %s)
                ) AS low_stock_product_count
        """, (DEFAULT_REORDER_LEVEL,))
        row = cursor.fetchone()
        metrics = {
            "total_products": row[0] or 0,
            "total_stock_units": row[1] or 0,
            "total_sales_transactions": row[2] or 0,
            "total_revenue": row[3] or 0,
            "estimated_gross_profit": row[4] or 0,
            "low_stock_product_count": row[5] or 0,
        }

        cursor.execute("""
            SELECT product_name, category,
                   COALESCE(stock_quantity, 0) AS stock_quantity,
                   COALESCE(reorder_level, %s) AS reorder_level
            FROM Products
            WHERE COALESCE(stock_quantity, 0)
                  <= COALESCE(reorder_level, %s)
            ORDER BY stock_quantity, product_name
            LIMIT %s
        """, (DEFAULT_REORDER_LEVEL, DEFAULT_REORDER_LEVEL, 12))
        low_stock_products = cursor.fetchall()

    return {"metrics": metrics, "low_stock_products": low_stock_products}


def get_monthly_sales_totals():
    """Return chronologically ordered (YYYY-MM, revenue, estimated_profit) tuples."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                DATE_FORMAT(s.sale_date, '%Y-%m') AS sale_month,
                COALESCE(SUM(si.quantity * si.selling_price), 0)
                    AS monthly_revenue,
                COALESCE(
                    SUM(
                        si.quantity *
                        (si.selling_price - si.purchase_price)
                    ),
                    0
                ) AS monthly_estimated_profit
            FROM Sales AS s
            JOIN Sale_Items AS si ON si.sale_id = s.sale_id
            GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
            ORDER BY sale_month
        """)
        return cursor.fetchall()


def get_top_selling_products(limit=10):
    """Return (product_name, units_sold) tuples ranked by units sold."""
    limit = _positive_integer(limit, "Limit")
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT p.product_name,
                   SUM(si.quantity) AS units_sold
            FROM Sale_Items AS si
            JOIN Products AS p ON p.product_id = si.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY units_sold DESC, p.product_name
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()


def get_stock_distribution_by_category():
    """Return (category, stock_units) tuples, including uncategorized products."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                CASE
                    WHEN category IS NULL OR TRIM(category) = ''
                    THEN 'Uncategorized'
                    ELSE category
                END AS product_category,
                COALESCE(SUM(stock_quantity), 0) AS stock_units
            FROM Products
            GROUP BY product_category
            ORDER BY stock_units DESC, product_category
        """)
        return cursor.fetchall()


def get_sales_history():
    """Return tuples matching the existing Sales History page columns."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                s.sale_id,
                s.sale_date,
                s.customer_name,
                p.product_name,
                si.quantity,
                si.selling_price,
                si.quantity * si.selling_price AS revenue,
                si.quantity *
                    (si.selling_price - si.purchase_price)
                    AS estimated_gross_profit
            FROM Sales AS s
            JOIN Sale_Items AS si ON si.sale_id = s.sale_id
            JOIN Products AS p ON p.product_id = si.product_id
            ORDER BY s.sale_date DESC, s.sale_id DESC
        """)
        return cursor.fetchall()


def get_sales_performance():
    """Return summary, monthly totals, and top-selling product results."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM Sales) AS total_sales_transactions,
                (
                    SELECT COALESCE(SUM(quantity * selling_price), 0)
                    FROM Sale_Items
                ) AS total_revenue,
                (
                    SELECT COALESCE(
                        SUM(quantity * (selling_price - purchase_price)),
                        0
                    )
                    FROM Sale_Items
                ) AS estimated_gross_profit
        """)
        summary_row = cursor.fetchone()

        cursor.execute("""
            SELECT
                DATE_FORMAT(s.sale_date, '%Y-%m') AS sale_month,
                COALESCE(SUM(si.quantity * si.selling_price), 0)
                    AS monthly_revenue,
                COALESCE(
                    SUM(
                        si.quantity *
                        (si.selling_price - si.purchase_price)
                    ),
                    0
                ) AS monthly_estimated_profit
            FROM Sales AS s
            JOIN Sale_Items AS si ON si.sale_id = s.sale_id
            GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
            ORDER BY sale_month
        """)
        monthly_totals = cursor.fetchall()

        cursor.execute("""
            SELECT p.product_name,
                   SUM(si.quantity) AS units_sold
            FROM Sale_Items AS si
            JOIN Products AS p ON p.product_id = si.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY units_sold DESC, p.product_name
            LIMIT %s
        """, (10,))
        top_selling_products = cursor.fetchall()

    return {
        "summary": {
            "total_sales_transactions": summary_row[0] or 0,
            "total_revenue": summary_row[1] or 0,
            "estimated_gross_profit": summary_row[2] or 0,
        },
        "monthly_totals": monthly_totals,
        "top_selling_products": top_selling_products,
    }


def get_revenue_report():
    """Return totals and chronological monthly rows for the report page."""
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM Sales) AS total_sales_transactions,
                (
                    SELECT COALESCE(SUM(quantity * selling_price), 0)
                    FROM Sale_Items
                ) AS total_revenue,
                (
                    SELECT COALESCE(
                        SUM(quantity * (selling_price - purchase_price)),
                        0
                    )
                    FROM Sale_Items
                ) AS estimated_gross_profit
        """)
        summary_row = cursor.fetchone()

        cursor.execute("""
            SELECT
                DATE_FORMAT(s.sale_date, '%Y-%m') AS sale_month,
                COALESCE(SUM(si.quantity * si.selling_price), 0)
                    AS monthly_revenue,
                COALESCE(
                    SUM(
                        si.quantity *
                        (si.selling_price - si.purchase_price)
                    ),
                    0
                ) AS monthly_estimated_profit
            FROM Sales AS s
            JOIN Sale_Items AS si ON si.sale_id = s.sale_id
            GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
            ORDER BY sale_month
        """)
        monthly_totals = cursor.fetchall()

    return {
        "summary": {
            "total_sales_transactions": summary_row[0] or 0,
            "total_revenue": summary_row[1] or 0,
            "estimated_gross_profit": summary_row[2] or 0,
        },
        "monthly_totals": monthly_totals,
    }


def get_analytics_data():
    """Return all datasets required by the existing Analytics page.

    Result keys and tuple row shapes match InventoryApp._fetch_analytics_data:
    monthly: (month, revenue, estimated_profit)
    best_sellers: (product_name, units_sold)
    category_stock: (category, stock_units)
    low_stock: (product_name, stock_quantity, reorder_level)
    """
    with _database_cursor() as (_, cursor):
        cursor.execute("""
            SELECT
                DATE_FORMAT(s.sale_date, '%Y-%m') AS sale_month,
                COALESCE(SUM(si.quantity * si.selling_price), 0)
                    AS monthly_revenue,
                COALESCE(
                    SUM(
                        si.quantity *
                        (si.selling_price - si.purchase_price)
                    ),
                    0
                ) AS monthly_estimated_profit
            FROM Sales AS s
            JOIN Sale_Items AS si ON si.sale_id = s.sale_id
            GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
            ORDER BY sale_month
        """)
        monthly = cursor.fetchall()

        cursor.execute("""
            SELECT p.product_name,
                   SUM(si.quantity) AS units_sold
            FROM Sale_Items AS si
            JOIN Products AS p ON p.product_id = si.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY units_sold DESC, p.product_name
            LIMIT %s
        """, (10,))
        best_sellers = cursor.fetchall()

        cursor.execute("""
            SELECT
                CASE
                    WHEN category IS NULL OR TRIM(category) = ''
                    THEN 'Uncategorized'
                    ELSE category
                END AS product_category,
                COALESCE(SUM(stock_quantity), 0) AS stock_units
            FROM Products
            GROUP BY product_category
            ORDER BY stock_units DESC, product_category
        """)
        category_stock = cursor.fetchall()

        cursor.execute("""
            SELECT product_name,
                   COALESCE(stock_quantity, 0) AS stock_quantity,
                   COALESCE(reorder_level, %s) AS reorder_level
            FROM Products
            WHERE COALESCE(stock_quantity, 0)
                  <= COALESCE(reorder_level, %s)
            ORDER BY stock_quantity, product_name
            LIMIT %s
        """, (DEFAULT_REORDER_LEVEL, DEFAULT_REORDER_LEVEL, 15))
        low_stock = cursor.fetchall()

    return {
        "monthly": monthly,
        "best_sellers": best_sellers,
        "category_stock": category_stock,
        "low_stock": low_stock,
    }


def record_sale(product_id, quantity, customer_name="Walk-in Customer"):
    """Record one sale and reduce stock atomically.

    Returns a dictionary containing sale_id, product_name, quantity,
    total_amount, and estimated_gross_profit. Prices are copied from Products
    into Sale_Items at sale time, preserving the existing historical model.
    """
    product_id = _positive_integer(product_id, "Product ID")
    quantity = _positive_integer(quantity, "Quantity")
    customer_name = str(customer_name or "Walk-in Customer").strip()
    if not customer_name:
        customer_name = "Walk-in Customer"

    with _database_cursor(transaction=True) as (connection, cursor):
        cursor.execute("""
            SELECT product_name, stock_quantity,
                   selling_price, purchase_price
            FROM Products
            WHERE product_id = %s
            FOR UPDATE
        """, (product_id,))
        product = cursor.fetchone()
        if product is None:
            raise ProductNotFoundError(f"Product ID {product_id} was not found.")

        product_name, stock_quantity, selling_price, purchase_price = product
        if quantity > int(stock_quantity or 0):
            raise InsufficientStockError(
                f"Insufficient stock for {product_name}. "
                f"Available: {stock_quantity}."
            )

        total_amount = Decimal(str(selling_price)) * quantity
        estimated_gross_profit = (
            Decimal(str(selling_price)) - Decimal(str(purchase_price))
        ) * quantity

        cursor.execute("""
            INSERT INTO Sales (customer_name, total_amount)
            VALUES (%s, %s)
        """, (customer_name, total_amount))
        sale_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO Sale_Items
            (sale_id, product_id, quantity,
             selling_price, purchase_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            sale_id,
            product_id,
            quantity,
            selling_price,
            purchase_price,
        ))

        cursor.execute("""
            UPDATE Products
            SET stock_quantity = stock_quantity - %s
            WHERE product_id = %s
              AND stock_quantity >= %s
        """, (quantity, product_id, quantity))
        if cursor.rowcount != 1:
            raise InsufficientStockError(
                "Stock changed before the sale completed. Please retry."
            )

        connection.commit()
        return {
            "sale_id": sale_id,
            "product_name": product_name,
            "quantity": quantity,
            "total_amount": total_amount,
            "estimated_gross_profit": estimated_gross_profit,
        }
