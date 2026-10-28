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

        # Seed essential popular medicines if not present so quotes and order items always match
        popular_seeds = [
            (169, "Dolo 650 650mg Tablet", "Paracetamol", "Micro Labs Ltd", "Analgesic", "Tablet", "650mg", "Paracetamol 650mg", "Strip of 15 tablets", 34.00, 0),
            (1002, "Electral Powder", "Oral Rehydration Salts", "FDC Ltd", "Hydration", "Powder", "21.8g Sachet", "Oral Rehydration Salts IP (WHO formula)", "sachet of 21.8 gm", 22.00, 0),
            (380, "Limcee 500mg Chewable Tablet", "Vitamin C + Zinc", "Abbott", "Immunity", "Tablet", "500mg", "Ascorbic Acid 500mg + Sodium Ascorbate", "strip of 15 tablets", 25.00, 0),
            (1004, "Prolyte ORS Ready Drink", "ORS Drink Apple Flavor", "Cipla Health Ltd", "Hydration", "Liquid", "200ml", "Electrolytes + Dextrose", "tetrapack of 200 ml", 32.00, 0),
            (148, "Combiflam 400mg/325mg Tablet", "Ibuprofen + Paracetamol", "Sanofi India", "Pain Relief", "Tablet", "Combo", "Ibuprofen 400mg + Paracetamol 325mg", "strip of 20 tablets", 45.00, 0),
            (19, "Azithral 500 Tablet", "Azithromycin", "Alembic Pharma", "Antibiotic", "Tablet", "500mg", "Azithromycin 500mg", "strip of 5 tablets", 119.50, 1),
            (487, "Pan 40 40mg Tablet", "Pantoprazole", "Alkem Laboratories", "Gastro", "Tablet", "40mg", "Pantoprazole Sodium 40mg", "strip of 15 tablets", 155.00, 0),
            (3, "Cetirizine 10mg Tablet", "Cetirizine Hydrochloride", "Cipla Ltd", "Allergy", "Tablet", "10mg", "Cetirizine HCl 10mg", "strip of 10 tablets", 18.00, 0),
            (1009, "Crocin 650 Advance", "Paracetamol", "GSK", "Analgesic", "Tablet", "650mg", "Fast-acting Paracetamol 650mg", "strip of 15 tablets", 32.50, 0),
            (122, "Calpol 650 Tablet", "Paracetamol", "GlaxoSmithKline", "Analgesic", "Tablet", "650mg", "Paracetamol 650mg", "strip of 15 tablets", 31.00, 0),
            (91, "Becosules Z Capsules", "B-Complex + Zinc", "Pfizer", "Vitamins", "Capsule", "Standard", "Vitamin B-Complex with Zinc & Vitamin C", "strip of 20 capsules", 52.00, 0),
            (548, "Supradyn Daily Multivitamin", "Multivitamin + Minerals", "Bayer", "Vitamins", "Tablet", "Daily", "Multivitamins with Minerals and Trace Elements", "strip of 15 tablets", 65.00, 0),
            (1013, "Zincovit Tablet", "Multivitamin + Zinc + Grape Seed", "Apex Laboratories", "Vitamins", "Tablet", "Standard", "Nutritional Health Supplement", "strip of 15 tablets", 110.00, 0),
            (7, "Augmentin 625 Duo Tablet", "Amoxicillin + Clavulanic Acid", "GSK", "Antibiotic", "Tablet", "625mg", "Amoxicillin 500mg + Clavulanate 125mg", "strip of 10 tablets", 223.00, 1),
            (491, "Pantocid 40mg Tablet", "Pantoprazole", "Sun Pharma", "Gastro", "Tablet", "40mg", "Pantoprazole 40mg", "strip of 15 tablets", 160.00, 0),
            (453, "Omez 20mg Capsule", "Omeprazole", "Dr. Reddy's", "Gastro", "Capsule", "20mg", "Omeprazole 20mg", "strip of 20 capsules", 68.00, 0),
            (294, "Gelusil MPS Antacid Liquid", "Aluminium + Magnesium + Dimethicone", "Pfizer", "Gastro", "Liquid", "200ml", "Acidity & Gas Relief Mint Flavor", "bottle of 200 ml", 128.00, 0),
            (182, "Digene Acidity Relief Liquid", "Antacid & Antigas", "Abbott", "Gastro", "Liquid", "200ml", "Aluminium Hydroxide + Magnesium Hydroxide", "bottle of 200 ml", 135.00, 0),
            (36, "Allegra 120mg Tablet", "Fexofenadine HCl", "Sanofi India", "Allergy", "Tablet", "120mg", "Fexofenadine Hydrochloride 120mg", "strip of 10 tablets", 215.00, 0),
            (397, "Montair LC 10mg/5mg Tablet", "Montelukast + Levocetirizine", "Cipla", "Allergy", "Tablet", "Combo", "Montelukast 10mg + Levocetirizine 5mg", "strip of 10 tablets", 220.00, 1),
            (555, "Sinarest New Tablet", "Cold Relief", "Centaur Pharma", "Cold & Flu", "Tablet", "Standard", "Paracetamol 500mg + Phenylephrine 10mg + CPM 2mg", "strip of 10 tablets", 64.00, 0),
            (107, "Benadryl Cough Syrup", "Diphenhydramine HCl", "Johnson & Johnson", "Cough", "Liquid", "100ml", "Diphenhydramine + Ammonium Chloride", "bottle of 100 ml", 125.00, 0),
            (71, "Ascoril D Plus Syrup", "Cough Relief", "Glenmark", "Cough", "Liquid", "100ml", "Dextromethorphan + Phenylephrine + CPM", "bottle of 100 ml", 132.00, 0),
            (1024, "Cofsils Lozenges Ginger Lemon", "Throat Lozenge", "Cipla Health", "Throat", "Lozenges", "Standard", "Amylmetacresol 0.6mg + Dichlorobenzyl Alcohol 1.2mg", "strip of 10 lozenges", 35.00, 0),
            (1025, "Vicks VapoRub", "Cold Balm", "Procter & Gamble", "Cold Relief", "Ointment", "50g", "Menthol + Camphor + Eucalyptus Oil", "jar of 50 gm", 165.00, 0),
            (391, "Meftal Spas 250mg/10mg Tablet", "Mefenamic Acid + Dicyclomine", "Blue Cross Labs", "Pain Relief", "Tablet", "Combo", "Mefenamic Acid 250mg + Dicyclomine HCl 10mg", "strip of 10 tablets", 53.00, 0),
            (623, "Volini Pain Relief Gel", "Diclofenac Gel", "Sun Pharma", "Pain Relief", "Gel", "50g", "Diclofenac Diethylamine 1.16% w/w", "tube of 50 gm", 170.00, 0),
            (544, "Shelcal 500 Tablet", "Calcium + Vitamin D3", "Torrent Pharma", "Bone Health", "Tablet", "500mg", "Calcium Carbonate 1250mg + Vitamin D3 250 IU", "strip of 15 tablets", 131.00, 0),
            (1029, "Saridon Headache Tablet", "Paracetamol + Propyphenazone", "Piramal Healthcare", "Pain Relief", "Tablet", "Standard", "Paracetamol 250mg + Propyphenazone 150mg + Caffeine 50mg", "strip of 10 tablets", 46.00, 0),
            (1030, "Disprin Regular Tablet", "Aspirin", "Reckitt Benckiser", "Pain Relief", "Tablet", "350mg", "Acetylsalicylic Acid 350mg", "strip of 10 tablets", 14.00, 0),
            (573, "Telma 40 Tablet", "Telmisartan", "Glenmark Pharma", "Cardiac", "Tablet", "40mg", "Telmisartan 40mg", "strip of 15 tablets", 225.00, 1),
            (278, "Glycomet 500 SR Tablet", "Metformin", "USV Ltd", "Diabetes", "Tablet", "500mg", "Metformin Hydrochloride 500mg", "strip of 20 tablets", 48.00, 1),
            (92, "Betadine 10% Ointment", "Povidone Iodine", "Win-Medicare", "Antiseptic", "Ointment", "20g", "Povidone-Iodine 10% w/w", "tube of 20 gm", 85.00, 0),
            (534, "Revital H Daily Health", "Ginseng + Minerals", "Sun Pharma", "Vitamins", "Capsule", "Daily", "Ginseng Extract with 10 Vitamins & 9 Minerals", "strip of 10 capsules", 115.00, 0),
            (1035, "Moov Pain Relief Cream", "Ayurvedic Pain Balm", "Reckitt Benckiser", "Pain Relief", "Cream", "50g", "Nilgiri Oil + Wintergreen Oil + Mint", "tube of 50 gm", 180.00, 0)
        ]
        for row in popular_seeds:
            db.execute("""
                INSERT OR IGNORE INTO medicines (id, name, generic_name, manufacturer, category, dosage_form, strength, composition, pack_size, mrp, requires_prescription)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        db.commit()
