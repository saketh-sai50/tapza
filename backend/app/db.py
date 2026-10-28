import sqlite3
from flask import g, current_app
from contextlib import contextmanager

def get_db():
    """Returns a per-request SQLite connection with WAL mode and foreign keys enabled."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=10.0 # Wait up to 10 seconds for locks to clear
        )
        g.db.row_factory = sqlite3.Row
        # Enable foreign key constraints and WAL mode for robust concurrency
        g.db.execute("PRAGMA foreign_keys = ON;")
        g.db.execute("PRAGMA journal_mode = WAL;")
    return g.db

def close_db(e=None):
    """Closes the current database connection if open."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

@contextmanager
def transaction(db=None):
    """
    Context manager for atomic database transactions with BEGIN IMMEDIATE
    to prevent race conditions on critical updates like single-pharmacy quote selection.
    """
    if db is None:
        db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE;")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

def init_db(app):
    """Initializes schema and default seed data."""
    with app.app_context():
        db = get_db()
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('CUSTOMER', 'PHARMACY', 'ADMIN')),
            phone TEXT,
            zone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Pharmacy profile details
        CREATE TABLE IF NOT EXISTS pharmacy_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            pharmacy_name TEXT NOT NULL,
            license_number TEXT NOT NULL,
            address TEXT NOT NULL,
            zone TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        -- Medicine Catalogue
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            generic_name TEXT,
            manufacturer TEXT,
            category TEXT,
            dosage_form TEXT,
            strength TEXT,
            composition TEXT,
            pack_size TEXT,
            mrp REAL NOT NULL,
            requires_prescription INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Customer Orders
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            zone TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN (
                'BROADCASTING',
                'PENDING_SELECTION',
                'CONFIRMED_PENDING_PHARMACY',
                'CONFIRMED',
                'REJECTED',
                'PREPARING',
                'DISPATCHED',
                'DELIVERED',
                'EXPIRED',
                'CANCELLED'
            )),
            broadcast_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            broadcast_expires_at TIMESTAMP NOT NULL,
            total_mrp REAL NOT NULL,
            final_amount REAL,
            mock_payment_status TEXT DEFAULT 'UNPAID' CHECK(mock_payment_status IN ('UNPAID', 'MOCK_PAID')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id) ON DELETE RESTRICT
        );

        -- Order items with original MRP
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_mrp REAL NOT NULL,
            subtotal_mrp REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (medicine_id) REFERENCES medicines (id) ON DELETE RESTRICT
        );

        -- Pharmacy Quotes
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            pharmacy_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'SUBMITTED' CHECK(status IN ('SUBMITTED', 'SELECTED', 'REJECTED', 'EXPIRED')),
            total_quoted_price REAL NOT NULL,
            available_items_count INTEGER NOT NULL,
            total_items_count INTEGER NOT NULL,
            is_full_fulfillment INTEGER NOT NULL,
            notes TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (pharmacy_id) REFERENCES users (id) ON DELETE RESTRICT,
            UNIQUE(order_id, pharmacy_id)
        );

        -- Quote Items (item-level pricing and availability)
        CREATE TABLE IF NOT EXISTS quote_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            order_item_id INTEGER NOT NULL,
            is_available INTEGER NOT NULL CHECK(is_available IN (0, 1)),
            unit_selling_price REAL NOT NULL DEFAULT 0.0,
            subtotal_price REAL NOT NULL DEFAULT 0.0,
            notes TEXT,
            FOREIGN KEY (quote_id) REFERENCES quotes (id) ON DELETE CASCADE,
            FOREIGN KEY (order_item_id) REFERENCES order_items (id) ON DELETE CASCADE
        );

        -- Order Assignments (strictly enforces 1-to-1 winning pharmacy quote assignment)
        CREATE TABLE IF NOT EXISTS order_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER UNIQUE NOT NULL,
            quote_id INTEGER UNIQUE NOT NULL,
            pharmacy_id INTEGER NOT NULL,
            selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmation_status TEXT DEFAULT 'PENDING' CHECK(confirmation_status IN ('PENDING', 'CONFIRMED', 'REJECTED')),
            confirmed_at TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (quote_id) REFERENCES quotes (id) ON DELETE CASCADE,
            FOREIGN KEY (pharmacy_id) REFERENCES users (id) ON DELETE RESTRICT
        );

        -- In-App Notifications
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            event_type TEXT NOT NULL,
            reference_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        -- Indexes for high-frequency queries
        CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_zone ON orders(zone);
        CREATE INDEX IF NOT EXISTS idx_quotes_order ON quotes(order_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
        """
        db.executescript(schema_sql)
        db.commit()

        # Ensure prescription columns exist on orders table
        order_cols = [c[1] for c in db.execute("PRAGMA table_info(orders)").fetchall()]
        if "order_type" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN order_type TEXT DEFAULT 'CATALOGUE'")
        if "prescription_url" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN prescription_url TEXT")
        if "prescription_notes" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN prescription_notes TEXT")
        if "is_ocr_scanned" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN is_ocr_scanned INTEGER DEFAULT 0")
        db.commit()

        # Seed default Admin account if not present
        from app.utils.auth_helpers import hash_password
        admin = db.execute("SELECT id FROM users WHERE email = ?", ("admin@tapza.com",)).fetchone()
        if not admin:
            db.execute("""
                INSERT INTO users (email, password_hash, full_name, role, phone, zone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "admin@tapza.com",
                hash_password("Admin@123"),
                "Tapza Administrator",
                "ADMIN",
                "+1-800-TAPZA-ADM",
                "CENTRAL"
            ))
            db.commit()
