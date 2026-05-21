import sys
import os
import sqlite3
from datetime import datetime

if hasattr(sys, '_MEIPASS'):
    # Running as bundle (PyInstaller)
    # We want the database to stay next to the .exe file, not in the Temp folder
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running in development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            category TEXT DEFAULT '',
            buy_price REAL NOT NULL DEFAULT 0,
            sell_price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER NOT NULL DEFAULT 5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            sell_price REAL NOT NULL,
            buy_price REAL NOT NULL,
            total REAL NOT NULL,
            profit REAL NOT NULL,
            sale_date TEXT DEFAULT (datetime('now', 'localtime')),
            is_paid INTEGER DEFAULT 1,
            customer_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration for existing sales table
    try:
        c.execute("ALTER TABLE sales ADD COLUMN is_paid INTEGER DEFAULT 1")
    except sqlite3.OperationalError: pass
    try:
        c.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
    except sqlite3.OperationalError: pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            min_stock INTEGER,
            status TEXT DEFAULT 'low',
            time TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Migration for notifications table
    try:
        c.execute("ALTER TABLE notifications ADD COLUMN status TEXT DEFAULT 'low'")
    except sqlite3.OperationalError: pass

    # Default settings
    defaults = [
        ("theme", "dark"),
        ("low_stock_threshold", "5"),
        ("currency", "DZD"),
        ("shop_name", "المتجر"),
        ("role", "user"),
        ("language", "ar"),
        ("admin_password", "admin123"),
        ("accent_color", "Orange"),
    ]
    for key, value in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    conn.close()

# ─── Settings ────────────────────────────────────────────────────────────────

def get_setting(key, default=""):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# ─── Products ─────────────────────────────────────────────────────────────────

def add_product(name, barcode, category, buy_price, sell_price, quantity, min_stock):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO products (name, barcode, category, buy_price, sell_price, quantity, min_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, barcode or None, category, buy_price, sell_price, quantity, min_stock))
        conn.commit()
        return True, "تمت إضافة المنتج بنجاح"
    except sqlite3.IntegrityError:
        return False, "الباركود مستخدم مسبقاً"
    finally:
        conn.close()

def update_product(product_id, name, barcode, category, buy_price, sell_price, quantity, min_stock):
    conn = get_connection()
    try:
        # Fetch old state to detect refill
        old = conn.execute("SELECT quantity, min_stock FROM products WHERE id=?", (product_id,)).fetchone()

        conn.execute("""
            UPDATE products SET name=?, barcode=?, category=?, buy_price=?, sell_price=?, quantity=?, min_stock=?
            WHERE id=?
        """, (name, barcode or None, category, buy_price, sell_price, quantity, min_stock, product_id))

        # Check for refill notification
        if old and old["quantity"] <= old["min_stock"] and quantity > min_stock:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                conn.execute("""
                    INSERT INTO notifications (product_id, product_name, quantity, min_stock, status, time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (product_id, name, quantity, min_stock, 'refilled', now))
            except sqlite3.OperationalError:
                # Fallback if status column doesn't exist yet
                conn.execute("""
                    INSERT INTO notifications (product_id, product_name, quantity, min_stock, time)
                    VALUES (?, ?, ?, ?, ?)
                """, (product_id, name, quantity, min_stock, now))

        conn.commit()
        return True, "تم تحديث المنتج"
    except sqlite3.IntegrityError:
        return False, "الباركود مستخدم مسبقاً"
    except Exception as e:
        print(f"Database Error in update_product: {e}")
        return False, str(e)
    finally:
        conn.close()

def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def get_all_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product_by_barcode(barcode):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE barcode=?", (barcode,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_product_by_id(product_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def search_products(query):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM products
        WHERE name LIKE ? OR barcode LIKE ? OR category LIKE ?
        ORDER BY name
    """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_low_stock_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products WHERE quantity <= min_stock ORDER BY quantity").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── Notifications ────────────────────────────────────────────────────────────

def log_notification(product_id, name, qty, min_stock):
    conn = get_connection()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("""
        INSERT INTO notifications (product_id, product_name, quantity, min_stock, time)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, name, qty, min_stock, now))
    conn.commit()
    conn.close()

def get_notifications():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notifications ORDER BY time DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_notifications():
    conn = get_connection()
    conn.execute("DELETE FROM notifications")
    conn.commit()
    conn.close()

# ─── Sales ────────────────────────────────────────────────────────────────────

def confirm_sale(product_id, qty, timestamp=None, is_paid=1, customer_id=None):
    conn = get_connection()
    try:
        product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not product:
            return False, "المنتج غير موجود"
        if product["quantity"] < qty:
            return False, "الكمية غير كافية في المخزون"

        total = product["sell_price"] * qty
        profit = (product["sell_price"] - product["buy_price"]) * qty
        now = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn.execute("""
            INSERT INTO sales (product_id, product_name, quantity, sell_price, buy_price, total, profit, sale_date, is_paid, customer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, product["name"], qty, product["sell_price"], product["buy_price"], total, profit, now, is_paid, customer_id))

        new_qty = product["quantity"] - qty
        conn.execute("UPDATE products SET quantity = ? WHERE id=?", (new_qty, product_id))

        # Check for low stock after sale using already fetched min_stock
        if new_qty <= product["min_stock"]:
            try:
                conn.execute("""
                    INSERT INTO notifications (product_id, product_name, quantity, min_stock, status, time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (product_id, product["name"], new_qty, product["min_stock"], 'low', now))
            except sqlite3.OperationalError:
                # Fallback for old schema if migration hasn't applied yet
                conn.execute("""
                    INSERT INTO notifications (product_id, product_name, quantity, min_stock, time)
                    VALUES (?, ?, ?, ?, ?)
                """, (product_id, product["name"], new_qty, product["min_stock"], now))

        conn.commit()
        return True, f"تم تأكيد البيع | الإجمالي: {total:.2f}"
    except Exception as e:
        print(f"Database Error in confirm_sale: {e}")
        return False, str(e)
    finally:
        conn.close()

def delete_sale_group(sale_date):
    """Deletes all sales recorded at a specific timestamp and restores their quantities."""
    conn = get_connection()
    sales = conn.execute("SELECT product_id, quantity FROM sales WHERE sale_date=?", (sale_date,)).fetchall()
    if sales:
        for s in sales:
            conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (s["quantity"], s["product_id"]))
        conn.execute("DELETE FROM sales WHERE sale_date=?", (sale_date,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def delete_sale_group_record(sale_date):
    """Deletes all sales recorded at a specific timestamp WITHOUT restoring quantities."""
    conn = get_connection()
    conn.execute("DELETE FROM sales WHERE sale_date=?", (sale_date,))
    conn.commit()
    conn.close()
    return True

def delete_sale(sale_id):
    """Deletes a sale and restores product quantity."""
    conn = get_connection()
    sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    if sale:
        conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?",
                     (sale["quantity"], sale["product_id"]))
        conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def delete_sale_record(sale_id):
    """Deletes a sale record WITHOUT restoring product quantity."""
    conn = get_connection()
    conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
    conn.commit()
    conn.close()
    return True

def delete_sales_by_year(year):
    """Deletes all sales for a specific year and RESTORES product quantities."""
    conn = get_connection()
    try:
        # Fetch all sales for that year first to restore quantities
        sales = conn.execute("SELECT product_id, quantity FROM sales WHERE strftime('%Y', sale_date)=?", (str(year),)).fetchall()
        for sale in sales:
            conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (sale["quantity"], sale["product_id"]))

        # Delete the records
        conn.execute("DELETE FROM sales WHERE strftime('%Y', sale_date)=?", (str(year),))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_sales_by_month(year, month):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM sales
        WHERE strftime('%Y', sale_date)=? AND strftime('%m', sale_date)=?
        ORDER BY sale_date DESC
    """, (str(year), f"{month:02d}")).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_monthly_summary(year):
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            CAST(strftime('%m', sale_date) AS INTEGER) as month,
            SUM(total) as revenue,
            SUM(profit) as profit,
            COUNT(*) as count
        FROM sales
        WHERE strftime('%Y', sale_date)=? AND is_paid=1
        GROUP BY month
        ORDER BY month
    """, (str(year),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_today_summary():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute("""
        SELECT COUNT(*) as count, SUM(total) as revenue, SUM(profit) as profit
        FROM sales WHERE DATE(sale_date) = ? AND is_paid=1
    """, (today,)).fetchone()
    conn.close()
    return dict(row) if row else {"count": 0, "revenue": 0, "profit": 0}

def get_products_count():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as count FROM products").fetchone()
    conn.close()
    return row["count"] if row else 0

def get_monthly_summary_total(year, month):
    conn = get_connection()
    row = conn.execute("""
        SELECT SUM(total) as revenue, SUM(profit) as profit
        FROM sales
        WHERE strftime('%Y', sale_date)=? AND strftime('%m', sale_date)=? AND is_paid=1
    """, (str(year), f"{month:02d}")).fetchone()
    conn.close()
    return dict(row) if row else {"revenue": 0, "profit": 0}

def get_total_summary():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as count, SUM(total) as revenue, SUM(profit) as profit FROM sales WHERE is_paid=1").fetchone()
    conn.close()
    return dict(row) if row else {"count": 0, "revenue": 0, "profit": 0}

# ─── Customers & Debts ──────────────────────────────────────────────────────

def add_customer(name, phone=""):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
        return True, "تمت إضافة الزبون"
    except sqlite3.IntegrityError:
        return False, "الزبون موجود مسبقاً"
    finally:
        conn.close()

def get_all_customers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_by_name(name):
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE name=?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_customers_summary():
    conn = get_connection()
    # Get all customers and their total debt (0 if no unpaid sales)
    rows = conn.execute("""
        SELECT c.*, COALESCE(SUM(s.total), 0) as total_debt
        FROM customers c
        LEFT JOIN sales s ON c.id = s.customer_id AND s.is_paid = 0
        GROUP BY c.id
        ORDER BY total_debt DESC, c.name ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_history(customer_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM sales
        WHERE customer_id = ?
        ORDER BY sale_date DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_sale_group_as_paid(customer_id, sale_date):
    conn = get_connection()
    conn.execute("UPDATE sales SET is_paid = 1 WHERE customer_id = ? AND sale_date = ?", (customer_id, sale_date))
    conn.commit()
    conn.close()
    return True

def delete_customer(customer_id):
    conn = get_connection()
    # Check if customer has any unpaid sales first?
    # Or just delete and set customer_id to NULL in sales?
    # Better to prevent deletion if they have debts, or just allow it.
    conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.execute("UPDATE sales SET customer_id = NULL WHERE customer_id=?", (customer_id,))
    conn.commit()
    conn.close()
    return True

def get_top_selling_products(limit=5):
    conn = get_connection()
    rows = conn.execute("""
        SELECT product_name, SUM(quantity) as total_qty
        FROM sales
        GROUP BY product_id
        ORDER BY total_qty DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_most_profitable_products(limit=5):
    conn = get_connection()
    rows = conn.execute("""
        SELECT product_name, SUM(profit) as total_profit
        FROM sales
        WHERE is_paid = 1
        GROUP BY product_id
        ORDER BY total_profit DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_category_distribution():
    conn = get_connection()
    rows = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM products
        GROUP BY category
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
