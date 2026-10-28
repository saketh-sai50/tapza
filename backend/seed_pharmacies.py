import csv
from io import StringIO
from app import create_app
from app.db import get_db, transaction
from app.utils.auth_helpers import hash_password

CSV_DATA = """Test_Pharmacy_ID,Pharmacy_Name,Zone,Address,Phone_Number_Test_Only,Phone_Status,Username,Password_TEST_ONLY,Login_Role,Data_Type,Active
TEST-PH-001,Sri Lakshmi Care Pharmacy,Warangal,"Plot 12, Demo Market Road, Warangal",9000000001,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm001,testpharm@001,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-002,Green Cross Medicals,Warangal,"Shop 4, Sample Colony Main Road, Warangal",9000000002,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm002,testpharm@002,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-003,CityWell Pharmacy,Warangal,"Door 8-1, Fictional Fort Road, Warangal",9000000003,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm003,testpharm@003,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-004,Aarogya Plus Medical Store,Warangal,"Shop 2, Demo Junction, Warangal",9000000004,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm004,testpharm@004,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-005,People's Health Pharmacy,Warangal,"Plot 19, Example Nagar, Warangal",9000000005,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm005,testpharm@005,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-006,MediBridge Medicals,Warangal,"Shop 6, Placeholder Street, Warangal",9000000006,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm006,testpharm@006,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-007,Sunrise Family Pharmacy,Warangal,"Door 3-5, Sample Enclave, Warangal",9000000007,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm007,testpharm@007,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-008,CarePoint Medicals,Warangal,"Shop 11, Demo Shopping Lane, Warangal",9000000008,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm008,testpharm@008,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-009,Vijaya Wellness Pharmacy,Warangal,"Plot 7, Fictional Residency Road, Warangal",9000000009,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm009,testpharm@009,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-010,TrustCare Medical Store,Warangal,"Shop 9, Example Circle, Warangal",9000000010,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm010,testpharm@010,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-011,PrimeLife Pharmacy,Warangal,"Door 2-8, Placeholder Colony, Warangal",9000000011,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm011,testpharm@011,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-012,HealthNest Medicals,Warangal,"Shop 5, Demo Park Road, Warangal",9000000012,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm012,testpharm@012,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-013,MedSpring Pharmacy,Warangal,"Plot 16, Sample Bazaar Street, Warangal",9000000013,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm013,testpharm@013,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-014,WellLeaf Medical Store,Warangal,"Shop 3, Fictional Cross Road, Warangal",9000000014,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm014,testpharm@014,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-015,CareSquare Pharmacy,Warangal,"Door 10-2, Example Layout, Warangal",9000000015,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm015,testpharm@015,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-016,Hanamkonda Health Hub,Hanamkonda,"Shop 1, Demo University Road, Hanamkonda",9000000016,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm016,testpharm@016,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-017,BlueCross Medicals,Hanamkonda,"Plot 14, Sample Chowk, Hanamkonda",9000000017,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm017,testpharm@017,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-018,FamilyFirst Pharmacy,Hanamkonda,"Door 6-2, Placeholder Main Road, Hanamkonda",9000000018,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm018,testpharm@018,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-019,MediBloom Medical Store,Hanamkonda,"Shop 8, Fictional Colony Road, Hanamkonda",9000000019,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm019,testpharm@019,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-020,Aarogya Care Pharmacy,Hanamkonda,"Plot 21, Example Nagar, Hanamkonda",9000000020,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm020,testpharm@020,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-021,WellnessWay Medicals,Hanamkonda,"Shop 7, Demo Market Lane, Hanamkonda",9000000021,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm021,testpharm@021,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-022,LifeLine Plus Pharmacy,Hanamkonda,"Door 4-9, Sample Residency, Hanamkonda",9000000022,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm022,testpharm@022,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-023,EverCare Medical Store,Hanamkonda,"Shop 12, Placeholder Junction, Hanamkonda",9000000023,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm023,testpharm@023,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-024,HealthHarbor Pharmacy,Hanamkonda,"Plot 5, Fictional Lake Road, Hanamkonda",9000000024,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm024,testpharm@024,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-025,MediCorner Medicals,Hanamkonda,"Shop 10, Example Street, Hanamkonda",9000000025,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm025,testpharm@025,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-026,GoodHealth Pharmacy,Hanamkonda,"Door 7-3, Demo Enclave, Hanamkonda",9000000026,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm026,testpharm@026,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-027,CareFirst Medical Store,Hanamkonda,"Plot 18, Sample Park Road, Hanamkonda",9000000027,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm027,testpharm@027,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-028,Namma Meds Pharmacy,Hanamkonda,"Shop 13, Placeholder Bazaar, Hanamkonda",9000000028,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm028,testpharm@028,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-029,WellSpring Medicals,Hanamkonda,"Door 9-1, Fictional Cross Lane, Hanamkonda",9000000029,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm029,testpharm@029,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-030,VitalCare Pharmacy,Hanamkonda,"Shop 15, Example Colony Road, Hanamkonda",9000000030,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm030,testpharm@030,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-031,Kazipet Care Pharmacy,Kazipet,"Shop 2, Demo Station Road, Kazipet",9000000031,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm031,testpharm@031,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-032,MediTrust Medicals,Kazipet,"Plot 9, Sample Main Street, Kazipet",9000000032,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm032,testpharm@032,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-033,HealthBridge Pharmacy,Kazipet,"Door 5-4, Placeholder Colony, Kazipet",9000000033,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm033,testpharm@033,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-034,CarePlus Medical Store,Kazipet,"Shop 14, Fictional Market Road, Kazipet",9000000034,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm034,testpharm@034,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-035,LifeSpring Pharmacy,Kazipet,"Plot 17, Example Junction, Kazipet",9000000035,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm035,testpharm@035,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-036,GoodCare Medicals,Kazipet,"Shop 6, Demo Enclave Road, Kazipet",9000000036,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm036,testpharm@036,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-037,MediRoots Pharmacy,Kazipet,"Door 3-7, Sample Residency, Kazipet",9000000037,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm037,testpharm@037,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-038,WellPath Medical Store,Kazipet,"Shop 9, Placeholder Street, Kazipet",9000000038,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm038,testpharm@038,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-039,FamilyCare Pharmacy,Kazipet,"Plot 22, Fictional Nagar Road, Kazipet",9000000039,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm039,testpharm@039,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-040,HealthFirst Medicals,Kazipet,"Shop 5, Example Bazaar, Kazipet",9000000040,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm040,testpharm@040,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-041,Aarogya Nest Pharmacy,Kazipet,"Door 8-6, Demo Colony, Kazipet",9000000041,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm041,testpharm@041,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-042,MediLane Medical Store,Kazipet,"Plot 11, Sample Park Lane, Kazipet",9000000042,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm042,testpharm@042,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-043,TrustWell Pharmacy,Kazipet,"Shop 16, Placeholder Cross Road, Kazipet",9000000043,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm043,testpharm@043,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-044,SunCare Medicals,Kazipet,"Door 2-3, Fictional Layout, Kazipet",9000000044,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm044,testpharm@044,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1
TEST-PH-045,PrimeCare Pharmacy,Kazipet,"Shop 4, Example Market Street, Kazipet",9000000045,SYNTHETIC TEST NUMBER - DO NOT CALL / WHATSAPP,testpharm045,testpharm@045,pharmacy,FICTIONAL DEMO DATA - NOT A REAL PHARMACY,1"""

def seed():
    print("=== Ingesting and Seeding 45 Test Pharmacies Across 3 Zones ===")
    app = create_app()

    with app.app_context():
        db = get_db()

        # Ensure username column exists
        cols = [c[1] for c in db.execute("PRAGMA table_info(users)").fetchall()]
        if "username" not in cols:
            db.execute("ALTER TABLE users ADD COLUMN username TEXT")
            db.commit()

        reader = csv.DictReader(StringIO(CSV_DATA))
        count = 0

        with transaction(db):
            for row in reader:
                pid = row["Test_Pharmacy_ID"].strip()
                name = row["Pharmacy_Name"].strip()
                zone = row["Zone"].strip()
                address = row["Address"].strip()
                phone = row["Phone_Number_Test_Only"].strip()
                username = row["Username"].strip()
                pwd = row["Password_TEST_ONLY"].strip()
                email = f"{username}@tapza.com"
                active = int(row["Active"])

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
                    db.execute(
                        """
                        UPDATE pharmacy_profiles
                        SET pharmacy_name = ?, license_number = ?, address = ?, zone = ?, is_active = ?
                        WHERE user_id = ?
                        """,
                        (name, pid, address, zone, active, u_id)
                    )
                else:
                    cur = db.execute(
                        """
                        INSERT INTO users (email, username, password_hash, full_name, role, phone, zone)
                        VALUES (?, ?, ?, ?, 'PHARMACY', ?, ?)
                        """,
                        (email, username, pwd_h, name, phone, zone)
                    )
                    u_id = cur.lastrowid
                    db.execute(
                        """
                        INSERT INTO pharmacy_profiles (user_id, pharmacy_name, license_number, address, zone, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (u_id, name, pid, address, zone, active)
                    )
                count += 1

        print(f"[SUCCESS] Successfully seeded {count} pharmacies across Warangal, Hanamkonda, and Kazipet!")

        # Verify counts per zone
        z_counts = db.execute("SELECT zone, COUNT(*) as c FROM pharmacy_profiles GROUP BY zone").fetchall()
        for z in z_counts:
            print(f"  • {z['zone']}: {z['c']} pharmacies active")

if __name__ == "__main__":
    seed()
