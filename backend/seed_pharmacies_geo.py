import math
import sqlite3
import os
from app import create_app
from app.db import get_db, transaction
from app.utils.auth_helpers import hash_password

PHARMACIES_GEO_DATA = [
    {
        "id": "TEST-PH-001",
        "name": "Sri Lasya Pharmacy",
        "zone": "Warangal",
        "address": "1-8-569, Opposite Water Tank, Nakkalagutta Main Road, Nakkalagutta, Warangal, Telangana 506001",
        "phone": "9000000001",
        "username": "testpharm001",
        "password": "testpharm@001",
        "lat": 18.002476,
        "lon": 79.556723
    },
    {
        "id": "TEST-PH-002",
        "name": "Care Pharmacy",
        "zone": "Warangal",
        "address": "H.No. 2, Junction, 5-378, Hanamkonda–Hyderabad Road, near Adalath Circle, S.V. Colony, Nakkalagutta, Hanamkonda, Telangana 506001",
        "phone": "9000000002",
        "username": "testpharm002",
        "password": "testpharm@002",
        "lat": 17.99529989,
        "lon": 79.54666189
    },
    {
        "id": "TEST-PH-003",
        "name": "Apollo Pharmacy — Circuit House Road",
        "zone": "Warangal",
        "address": "Door No. 2/5-813/B, Circuit House Road, K.L.N. Reddy Colony, Nakkalagutta, Hanamkonda, Telangana 506001",
        "phone": "9000000003",
        "username": "testpharm003",
        "password": "testpharm@003",
        "lat": 17.99756848,
        "lon": 79.54718374
    },
    {
        "id": "TEST-PH-004",
        "name": "Sri Venkateshwara Medical & General Stores",
        "zone": "Warangal",
        "address": "2-5-815, Circuit House Road, Nakkalagutta, Hanamkonda, Telangana 506001",
        "phone": "9000000004",
        "username": "testpharm004",
        "password": "testpharm@004",
        "lat": 17.99933987,
        "lon": 79.56159157
    },
    {
        "id": "TEST-PH-005",
        "name": "M R Pharmacy",
        "zone": "Warangal",
        "address": "2-5-205, Circuit House Road, Nakkalagutta, Hanamkonda, Telangana 506001",
        "phone": "9000000005",
        "username": "testpharm005",
        "password": "testpharm@005",
        "lat": 18.00305465,
        "lon": 79.55219074
    },
    {
        "id": "TEST-PH-006",
        "name": "MedPlus Central Excise Colony",
        "zone": "Warangal",
        "address": "H.No. 2/7/746, Devarpula–Hanamkonda Road, Excise Colony, Subedari, Hanamkonda, Telangana 506001",
        "phone": "9000000006",
        "username": "testpharm006",
        "password": "testpharm@006",
        "lat": 17.99778855,
        "lon": 79.54496755
    },
    {
        "id": "TEST-PH-007",
        "name": "Sri Sai Medical and General Stores",
        "zone": "Warangal",
        "address": "2, 7-463, Excise Colony, Subedari, Hanamkonda, Telangana 506001",
        "phone": "9000000007",
        "username": "testpharm007",
        "password": "testpharm@007",
        "lat": 17.97077590,
        "lon": 79.59300953
    },
    {
        "id": "TEST-PH-008",
        "name": "Sri Vidhya Generic Medicals",
        "zone": "Warangal",
        "address": "Circuit House Road, Subedari, Hanamkonda, Telangana 506001 (Plus Code XGXX+FJ7)",
        "phone": "9000000008",
        "username": "testpharm008",
        "password": "testpharm@008",
        "lat": 17.99890367,
        "lon": 79.54906175
    },
    {
        "id": "TEST-PH-009",
        "name": "Arogya Pharmacy",
        "zone": "Warangal",
        "address": "NH163, Postal Colony, Subedari, Hanamkonda, Telangana 506001 (Plus Code XGWX+7HP)",
        "phone": "9000000009",
        "username": "testpharm009",
        "password": "testpharm@009",
        "lat": 17.99587795,
        "lon": 79.54897288
    },
    {
        "id": "TEST-PH-010",
        "name": "Apollo Pharmacy — Adalath",
        "zone": "Warangal",
        "address": "D.No. 2-5-501, Main Road, Adalath, opposite Spencer Value Market, Hanamkonda, Telangana 506001",
        "phone": "9000000010",
        "username": "testpharm010",
        "password": "testpharm@010",
        "lat": 17.99916797,
        "lon": 79.54427343
    },
    {
        "id": "TEST-PH-011",
        "name": "Sri Vinayaka Pharmacy",
        "zone": "Warangal",
        "address": "16-9-585/1, Bank Colony, Puppalagutta, Warangal, Telangana 506002",
        "phone": "9000000011",
        "username": "testpharm011",
        "password": "testpharm@011",
        "lat": 17.96812957,
        "lon": 79.61050905
    },
    {
        "id": "TEST-PH-012",
        "name": "Apollo Pharmacy — Mandi Market",
        "zone": "Warangal",
        "address": "No. 14/5/4, Main Road, near Martha Siddhan Mart, Sherpura, Warangal, Telangana 506002",
        "phone": "9000000012",
        "username": "testpharm012",
        "password": "testpharm@012",
        "lat": 17.98764208,
        "lon": 79.59824693
    },
    {
        "id": "TEST-PH-013",
        "name": "Medi-Mart Pharmacy",
        "zone": "Warangal",
        "address": "RM Complex, 11-23-284, Narsampet Road, Kashibugga, Girmajipet, Warangal, Telangana 506002",
        "phone": "9000000013",
        "username": "testpharm013",
        "password": "testpharm@013",
        "lat": 17.98251557,
        "lon": 79.60567957
    },
    {
        "id": "TEST-PH-014",
        "name": "Value Health Care",
        "zone": "Warangal",
        "address": "3, Jayaprakash Narayan Road, Girmajipet, Warangal, Telangana 506002",
        "phone": "9000000014",
        "username": "testpharm014",
        "password": "testpharm@014",
        "lat": 17.98179416,
        "lon": 79.59897847
    },
    {
        "id": "TEST-PH-015",
        "name": "Reddy's Medicals & Surgicals",
        "zone": "Warangal",
        "address": "1/A, 16-2-213, Kareemabad Road, beside SBI Bank, Kareemabad, Warangal, Telangana 506002",
        "phone": "9000000015",
        "username": "testpharm015",
        "password": "testpharm@015",
        "lat": 17.96972534,
        "lon": 79.59277246
    },
    {
        "id": "TEST-PH-016",
        "name": "Keerthy Medical Stores Pvt Ltd",
        "zone": "Hanamkonda",
        "address": "6-2-170, Main Road, opposite Men's Club Fashions, Chowrasta, Gandhi Nagar, Hanamkonda, Telangana 506001",
        "phone": "9000000016",
        "username": "testpharm016",
        "password": "testpharm@016",
        "lat": 18.00682863,
        "lon": 79.56947177
    },
    {
        "id": "TEST-PH-017",
        "name": "Jeevanlal & Sons Medical Stores",
        "zone": "Hanamkonda",
        "address": "R. Jeevanlal Complex, Main Road, Hanamkonda, Telangana 506011",
        "phone": "9000000017",
        "username": "testpharm017",
        "password": "testpharm@017",
        "lat": 18.00648354,
        "lon": 79.57004908
    },
    {
        "id": "TEST-PH-018",
        "name": "A2Z Medical & Surgicals",
        "zone": "Hanamkonda",
        "address": "Punnamchander Complex, 6-2-220, Chowrastha, Kakaji Nagar Colony, Hanamkonda, Telangana 506011",
        "phone": "9000000018",
        "username": "testpharm018",
        "password": "testpharm@018",
        "lat": 18.02156132,
        "lon": 79.54983472
    },
    {
        "id": "TEST-PH-019",
        "name": "Life Care Pharmacy",
        "zone": "Hanamkonda",
        "address": "NGO Colony Road, beside Life Line Hospital, Main Road, Ramnagar, Hanamkonda, Telangana 506001",
        "phone": "9000000019",
        "username": "testpharm019",
        "password": "testpharm@019",
        "lat": 18.00664556,
        "lon": 79.55566189
    },
    {
        "id": "TEST-PH-020",
        "name": "Vasu's Apple Pharmacy",
        "zone": "Hanamkonda",
        "address": "24-7-302/1/A/1, opposite Royal Enfield showroom, beside Miniso, Ramakrishna Colony, Revenue Colony, Subedari, Hanamkonda, Telangana 506001",
        "phone": "9000000020",
        "username": "testpharm020",
        "password": "testpharm@020",
        "lat": 17.99255805,
        "lon": 79.53660587
    },
    {
        "id": "TEST-PH-021",
        "name": "Sathish Medical Hall Generic",
        "zone": "Hanamkonda",
        "address": "Shop 07, Yadav Nagar, Reddy Colony, Hanamkonda, Telangana 506011",
        "phone": "9000000021",
        "username": "testpharm021",
        "password": "testpharm@021",
        "lat": 18.01616090,
        "lon": 79.57731800
    },
    {
        "id": "TEST-PH-022",
        "name": "Annapurna Pharmacy",
        "zone": "Hanamkonda",
        "address": "3-3-24, Chowrastha, Hanamkonda, Telangana 506001",
        "phone": "9000000022",
        "username": "testpharm022",
        "password": "testpharm@022",
        "lat": 17.99492323,
        "lon": 79.53094102
    },
    {
        "id": "TEST-PH-023",
        "name": "Naresh Medical Store",
        "zone": "Hanamkonda",
        "address": "Shop No. 2, New Bus Stand Road, Machili Bazar, Brahmanawada, Hanamkonda, Telangana 506001",
        "phone": "9000000023",
        "username": "testpharm023",
        "password": "testpharm@023",
        "lat": 18.00245447,
        "lon": 79.57286589
    },
    {
        "id": "TEST-PH-024",
        "name": "Medi Care Pharmacy and General Stores",
        "zone": "Hanamkonda",
        "address": "New Bus Stand Road, Laxmipuram, Kakaji Nagar Colony, Hanamkonda, Telangana 506001 (Plus Code 2H28+VXH)",
        "phone": "9000000024",
        "username": "testpharm024",
        "password": "testpharm@024",
        "lat": 18.00240216,
        "lon": 79.56746421
    },
    {
        "id": "TEST-PH-025",
        "name": "Natraj Medical Store",
        "zone": "Hanamkonda",
        "address": "K.L.N. Reddy Colony, Gokulnagar, Hanamkonda, Telangana 506001 (Plus Code 2G3X+4RX)",
        "phone": "9000000025",
        "username": "testpharm025",
        "password": "testpharm@025",
        "lat": 18.00308656,
        "lon": 79.54962325
    },
    {
        "id": "TEST-PH-026",
        "name": "Sri Ganesh Medical Agencies",
        "zone": "Hanamkonda",
        "address": "Srinivas Colony Road, Balasamudram, Hanamkonda, Telangana 506001",
        "phone": "9000000026",
        "username": "testpharm026",
        "password": "testpharm@026",
        "lat": 18.00319245,
        "lon": 79.54695008
    },
    {
        "id": "TEST-PH-027",
        "name": "Annapurna Medical and General Stores",
        "zone": "Hanamkonda",
        "address": "Hyderabad–Warangal Highway, Raganna Darwaja, Alankar, Kakatiya Colony, Hanamkonda, Telangana 506001",
        "phone": "9000000027",
        "username": "testpharm027",
        "password": "testpharm@027",
        "lat": 18.00353267,
        "lon": 79.57956960
    },
    {
        "id": "TEST-PH-028",
        "name": "Sri Laxmi Medical Store",
        "zone": "Hanamkonda",
        "address": "Unnamed Road, Balasamudram, Hanamkonda, Telangana 506001 (Plus Code 2H25V53)",
        "phone": "9000000028",
        "username": "testpharm028",
        "password": "testpharm@028",
        "lat": 18.00874044,
        "lon": 79.56850717
    },
    {
        "id": "TEST-PH-029",
        "name": "Trimed Pharmacy",
        "zone": "Hanamkonda",
        "address": "Teachers Colony Road, Waddepally Phase II, Teachers Colony, Hanamkonda, Telangana 506001",
        "phone": "9000000029",
        "username": "testpharm029",
        "password": "testpharm@029",
        "lat": 17.99713246,
        "lon": 79.53580987
    },
    {
        "id": "TEST-PH-030",
        "name": "Sri Laxmi Medical and General Store",
        "zone": "Hanamkonda",
        "address": "Vaddepalli, Gokulnagar, Hanamkonda, Telangana 506001",
        "phone": "9000000030",
        "username": "testpharm030",
        "password": "testpharm@030",
        "lat": 18.00495196,
        "lon": 79.54968565
    },
    {
        "id": "TEST-PH-031",
        "name": "Apollo Pharmacy — Kazipet Main Road",
        "zone": "Kazipet",
        "address": "D.No. 1-3-172, Main Road, Kazipet, Warangal District, Telangana 506003",
        "phone": "9000000031",
        "username": "testpharm031",
        "password": "testpharm@031",
        "lat": 17.97163609,
        "lon": 79.50017569
    },
    {
        "id": "TEST-PH-032",
        "name": "Apollo Pharmacy — Bapuji Nagar",
        "zone": "Kazipet",
        "address": "Ground Floor, D.No. 25-11-127, Main Road, Bapuji Nagar, Kazipet, Telangana 506003",
        "phone": "9000000032",
        "username": "testpharm032",
        "password": "testpharm@032",
        "lat": 17.97764000,
        "lon": 79.53074000
    },
    {
        "id": "TEST-PH-033",
        "name": "Apollo Pharmacy — Siddartha Nagar",
        "zone": "Kazipet",
        "address": "D.No. 1-1-904, Ground Floor, Siddartha Nagar, Fatima Nagar, NIT Post, Kazipet, Telangana 506003",
        "phone": "9000000033",
        "username": "testpharm033",
        "password": "testpharm@033",
        "lat": 18.01079400,
        "lon": 79.54627300
    },
    {
        "id": "TEST-PH-034",
        "name": "Apollo Pharmacy — Madikonda",
        "zone": "Kazipet",
        "address": "D.No. 30-2-353, Ground Floor, Hyderabad Road, Madikonda Village, Kazipet Mandal, Telangana 506003",
        "phone": "9000000034",
        "username": "testpharm034",
        "password": "testpharm@034",
        "lat": 17.96612428,
        "lon": 79.48788507
    },
    {
        "id": "TEST-PH-035",
        "name": "MedPlus Siddhartha Nagar",
        "zone": "Kazipet",
        "address": "D.No. 1-1-878, Siddhartha Nagar Main Road, Kazipet, Hanamkonda, Telangana 506004",
        "phone": "9000000035",
        "username": "testpharm035",
        "password": "testpharm@035",
        "lat": 17.98480589,
        "lon": 79.52199699
    },
    {
        "id": "TEST-PH-036",
        "name": "New Sri Sairam Medical and General Store",
        "zone": "Kazipet",
        "address": "Darga Chowrastha, NIT Campus Road, Kazipet, Hanamkonda, Telangana 506004 (Plus Code XGHM2W3)",
        "phone": "9000000036",
        "username": "testpharm036",
        "password": "testpharm@036",
        "lat": 17.97770527,
        "lon": 79.53476504
    },
    {
        "id": "TEST-PH-037",
        "name": "Sri Santosh Medical and General Stores",
        "zone": "Kazipet",
        "address": "Hyderabad–Warangal–Bhopalpatnam Road, Main Road, Siddhartha Nagar, Kazipet, Telangana 506004",
        "phone": "9000000037",
        "username": "testpharm037",
        "password": "testpharm@037",
        "lat": 17.97764000,
        "lon": 79.53074000
    },
    {
        "id": "TEST-PH-038",
        "name": "Netmeds Pharmacy",
        "zone": "Kazipet",
        "address": "Ground Floor, Shivananda Complex, Survey No. 352, Fatima Nagar, Kazipet, Telangana 506004",
        "phone": "9000000038",
        "username": "testpharm038",
        "password": "testpharm@038",
        "lat": 17.98622016,
        "lon": 79.52543674
    },
    {
        "id": "TEST-PH-039",
        "name": "Dhanvantari Medical",
        "zone": "Kazipet",
        "address": "Bapuji Nagar, Hyderabad–Warangal–Bhopalpatnam Highway, Kazipet, Telangana 506003 (Plus Code XGC2+H38)",
        "phone": "9000000039",
        "username": "testpharm039",
        "password": "testpharm@039",
        "lat": 17.97165501,
        "lon": 79.50023288
    },
    {
        "id": "TEST-PH-040",
        "name": "Swarna Generic Medical Shop",
        "zone": "Kazipet",
        "address": "Kazipet Main Road Junction, Kazipet, Telangana 506003",
        "phone": "9000000040",
        "username": "testpharm040",
        "password": "testpharm@040",
        "lat": 17.97604589,
        "lon": 79.50935257
    },
    {
        "id": "TEST-PH-041",
        "name": "Vijayalakshmi Medical Store",
        "zone": "Kazipet",
        "address": "30-1-220, Madikonda–Dharmasagaram Road, Madikonda, Kazipet, Telangana 506142",
        "phone": "9000000041",
        "username": "testpharm041",
        "password": "testpharm@041",
        "lat": 17.96467035,
        "lon": 79.48079071
    },
    {
        "id": "TEST-PH-042",
        "name": "Pharma Plus",
        "zone": "Kazipet",
        "address": "H.No. 81-3-109/1, Hyderabad–Warangal–Bhopalpatnam Road, Main Road, Rahamatnagar, Kazipet, Telangana 506003",
        "phone": "9000000042",
        "username": "testpharm042",
        "password": "testpharm@042",
        "lat": 17.97800749,
        "lon": 79.51154654
    },
    {
        "id": "TEST-PH-043",
        "name": "Rama Medical Hall",
        "zone": "Kazipet",
        "address": "1-5-103, Kazipet Main Road, Jubilee Market, Rahamatnagar, Kazipet, Telangana 506003",
        "phone": "9000000043",
        "username": "testpharm043",
        "password": "testpharm@043",
        "lat": 17.97586915,
        "lon": 79.50867928
    },
    {
        "id": "TEST-PH-044",
        "name": "Drug Mart Medicals",
        "zone": "Kazipet",
        "address": "Nehru Nagar, near Mettigutta Arch, Madikonda, Kazipet, Telangana 506003",
        "phone": "9000000044",
        "username": "testpharm044",
        "password": "testpharm@044",
        "lat": 17.96726089,
        "lon": 79.48947547
    },
    {
        "id": "TEST-PH-045",
        "name": "Devendra Medical and General Stores",
        "zone": "Kazipet",
        "address": "1-3-85/1, Main Road, Kazipet, Warangal District, Telangana 506003",
        "phone": "9000000045",
        "username": "testpharm045",
        "password": "testpharm@045",
        "lat": 17.97876180,
        "lon": 79.51276369
    }
]

def seed_geo():
    print("=== Migrating and Seeding 45 Real Pharmacies with Lat/Lon & SQLite R*Tree ===")
    app = create_app()

    with app.app_context():
        db = get_db()

        # 1. Ensure pharmacy_profiles has latitude, longitude, and phone columns
        prof_cols = [c[1] for c in db.execute("PRAGMA table_info(pharmacy_profiles)").fetchall()]
        if "latitude" not in prof_cols:
            db.execute("ALTER TABLE pharmacy_profiles ADD COLUMN latitude REAL")
        if "longitude" not in prof_cols:
            db.execute("ALTER TABLE pharmacy_profiles ADD COLUMN longitude REAL")
        if "phone" not in prof_cols:
            db.execute("ALTER TABLE pharmacy_profiles ADD COLUMN phone TEXT")

        # 2. Ensure orders table has spatial columns
        order_cols = [c[1] for c in db.execute("PRAGMA table_info(orders)").fetchall()]
        if "customer_lat" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN customer_lat REAL")
        if "customer_lng" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN customer_lng REAL")
        if "search_radius_km" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN search_radius_km REAL DEFAULT 5.0")
        if "expanded_at" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN expanded_at TIMESTAMP")

        # 3. Create R*Tree virtual table for pharmacies
        db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS pharmacy_rtree USING rtree(
                id,
                min_lat, max_lat,
                min_lng, max_lng
            );
        """)

        # 4. Create order_broadcast_pharmacies table
        db.execute("""
            CREATE TABLE IF NOT EXISTS order_broadcast_pharmacies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                pharmacy_id INTEGER NOT NULL,
                distance_km REAL NOT NULL,
                ring_stage INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (pharmacy_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(order_id, pharmacy_id)
            );
        """)
        db.commit()

        # 5. Seed / Upsert the 45 pharmacies
        count = 0
        with transaction(db):
            # Clear previous R*Tree to maintain clean indices
            db.execute("DELETE FROM pharmacy_rtree")

            for item in PHARMACIES_GEO_DATA:
                name = item["name"]
                zone = item["zone"]
                addr = item["address"]
                phone = item["phone"]
                username = item["username"]
                pwd = item["password"]
                email = f"{username}@tapza.com"
                lat = float(item["lat"])
                lon = float(item["lon"])
                pwd_h = hash_password(pwd)

                # Upsert user
                existing = db.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
                if existing:
                    u_id = existing["id"]
                    db.execute(
                        """
                        UPDATE users
                        SET email = ?, username = ?, password_hash = ?, full_name = ?, phone = ?, zone = ?
                        WHERE id = ?
                        """,
                        (email, username, pwd_h, name, phone, zone, u_id)
                    )
                else:
                    cursor = db.execute(
                        """
                        INSERT INTO users (email, username, password_hash, full_name, role, phone, zone)
                        VALUES (?, ?, ?, ?, 'PHARMACY', ?, ?)
                        """,
                        (email, username, pwd_h, name, phone, zone)
                    )
                    u_id = cursor.lastrowid

                # Upsert pharmacy profile
                p_prof = db.execute("SELECT id FROM pharmacy_profiles WHERE user_id = ?", (u_id,)).fetchone()
                lic_no = f"TS-WGL-{item['id']}"
                if p_prof:
                    db.execute(
                        """
                        UPDATE pharmacy_profiles
                        SET pharmacy_name = ?, license_number = ?, address = ?, zone = ?, is_active = 1,
                            latitude = ?, longitude = ?, phone = ?
                        WHERE user_id = ?
                        """,
                        (name, lic_no, addr, zone, lat, lon, phone, u_id)
                    )
                else:
                    db.execute(
                        """
                        INSERT INTO pharmacy_profiles (user_id, pharmacy_name, license_number, address, zone, is_active, latitude, longitude, phone)
                        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                        """,
                        (u_id, name, lic_no, addr, zone, lat, lon, phone)
                    )

                # Insert into R*Tree (point bounding box: min_lat = max_lat = lat)
                db.execute(
                    """
                    INSERT INTO pharmacy_rtree (id, min_lat, max_lat, min_lng, max_lng)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (u_id, lat, lat, lon, lon)
                )
                count += 1

        print(f"Successfully seeded and indexed {count} pharmacies in SQLite R*Tree!")

if __name__ == "__main__":
    seed_geo()
