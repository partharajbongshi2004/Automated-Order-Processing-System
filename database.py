import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

DB_NAME = "clothing_store.db"


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables and seed initial clothing inventory if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            size TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            UNIQUE(name, size)
        )
    """)

    # Create orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_message TEXT NOT NULL,
            product_name TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Seed initial stock if the products table is empty
    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()["count"] == 0:
        initial_products = [
            ("Classic Cotton T-Shirt", "S", 25.00, 15),
            ("Classic Cotton T-Shirt", "M", 25.00, 20),
            ("Classic Cotton T-Shirt", "L", 25.00, 12),
            ("Classic Cotton T-Shirt", "XL", 25.00, 8),
            ("Slim Fit Denim Jeans", "S", 60.00, 10),
            ("Slim Fit Denim Jeans", "M", 60.00, 14),
            ("Slim Fit Denim Jeans", "L", 60.00, 9),
            ("Slim Fit Denim Jeans", "XL", 60.00, 5),
            ("Oversized Fleece Hoodie", "S", 55.00, 7),
            ("Oversized Fleece Hoodie", "M", 55.00, 11),
            ("Oversized Fleece Hoodie", "L", 55.00, 15),
            ("Oversized Fleece Hoodie", "XL", 55.00, 6),
            ("Linen Summer Shirt", "S", 45.00, 8),
            ("Linen Summer Shirt", "M", 45.00, 10),
            ("Linen Summer Shirt", "L", 45.00, 6),
            ("Lightweight Windbreaker Jacket", "M", 85.00, 5),
            ("Lightweight Windbreaker Jacket", "L", 85.00, 7),
            ("Lightweight Windbreaker Jacket", "XL", 85.00, 4),
        ]
        cursor.executemany(
            "INSERT INTO products (name, size, price, stock) VALUES (?, ?, ?, ?)",
            initial_products,
        )

    conn.commit()
    conn.close()


def get_all_products() -> List[Dict]:
    """Fetch all products sorted by name and size."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY name, size")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_unique_product_names() -> List[str]:
    """Fetch a list of distinct product names in the catalog."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM products ORDER BY name")
    names = [row["name"] for row in cursor.fetchall()]
    conn.close()
    return names


def get_all_orders() -> List[Dict]:
    """Fetch all completed orders ordered by newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def check_stock(product_name: str, size: str, quantity: int) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validate if the product exists in the requested size and has enough stock.
    Returns: (is_available, status_message, product_dict)
    """
    if quantity <= 0:
        return False, "Quantity must be greater than zero.", None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE LOWER(name) = LOWER(?) AND UPPER(size) = UPPER(?)",
        (product_name.strip(), size.strip()),
    )
    product = cursor.fetchone()
    conn.close()

    if not product:
        return False, f"Product '{product_name}' in size '{size.upper()}' was not found in inventory.", None

    product_dict = dict(product)
    if product_dict["stock"] < quantity:
        return (
            False,
            f"Insufficient stock for {product_dict['name']} ({product_dict['size']}). "
            f"Requested: {quantity}, Available: {product_dict['stock']}.",
            product_dict,
        )

    return True, "In stock and ready to fulfill.", product_dict


def process_and_save_order(
    customer_message: str,
    product_id: int,
    product_name: str,
    size: str,
    quantity: int,
    unit_price: float,
) -> Dict:
    """
    Atomically reduce stock and record the new order in the database.
    Returns a dictionary containing the full order details for invoice generation.
    """
    conn = get_connection()
    cursor = conn.cursor()

    total_price = round(unit_price * quantity, 2)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    try:
        # Deduct stock safely
        cursor.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (quantity, product_id, quantity),
        )
        if cursor.rowcount == 0:
            raise ValueError("Stock update failed due to insufficient inventory.")

        # Insert order record
        cursor.execute(
            """
            INSERT INTO orders (
                order_number, customer_message, product_name, size,
                quantity, unit_price, total_price, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_number,
                customer_message,
                product_name,
                size.upper(),
                quantity,
                unit_price,
                total_price,
                created_at,
            ),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return {
        "order_number": order_number,
        "customer_message": customer_message,
        "product_name": product_name,
        "size": size.upper(),
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
        "created_at": created_at,
    }
