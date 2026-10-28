import json
from app import create_app
from app.db import get_db

app = create_app()

def run_tests():
    print("=== Testing Stage 2: Database Schema & Authentication ===")
    client = app.test_client()

    with app.app_context():
        db = get_db()
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"Created SQLite tables: {', '.join(sorted(tables))}")
        
        required_tables = [
            "users", "pharmacy_profiles", "medicines", "orders",
            "order_items", "quotes", "quote_items", "order_assignments", "notifications"
        ]
        for tbl in required_tables:
            assert tbl in tables, f"Missing required table: {tbl}"
        print("[OK] All required database schema tables verified.")

        # Check default admin seed
        admin = db.execute("SELECT id, email, role, full_name FROM users WHERE role = 'ADMIN'").fetchone()
        assert admin is not None, "Admin user was not seeded"
        assert admin["email"] == "admin@tapza.com"
        print(f"[OK] Default Admin verified: {admin['email']} (Role: {admin['role']})")

    # Test 1: Admin Login
    res = client.post("/api/auth/login", json={
        "email": "admin@tapza.com",
        "password": "Admin@123"
    })
    assert res.status_code == 200, f"Admin login failed: {res.data}"
    admin_data = res.get_json()
    admin_token = admin_data["token"]
    print("[OK] Admin login successful, JWT generated.")

    # Test 2: Customer Registration
    res = client.post("/api/auth/register", json={
        "email": "customer.test@example.com",
        "password": "Password123!",
        "full_name": "Jane Customer",
        "role": "CUSTOMER",
        "phone": "+1-555-0100",
        "zone": "ZONE_A"
    })
    assert res.status_code == 201, f"Customer registration failed: {res.data}"
    cust_data = res.get_json()
    cust_token = cust_data["token"]
    assert cust_data["user"]["role"] == "CUSTOMER"
    print("[OK] Customer registration verified with role CUSTOMER and ZONE_A.")

    # Test 3: Pharmacy Registration
    res = client.post("/api/auth/register", json={
        "email": "pharma.central@example.com",
        "password": "PharmacyPass123!",
        "full_name": "Robert Pharmacist",
        "role": "PHARMACY",
        "phone": "+1-555-0200",
        "zone": "ZONE_A",
        "pharmacy_name": "Apex Care Pharmacy",
        "license_number": "PHARM-LIC-2026-9901",
        "address": "450 Health Ave, Sector 4"
    })
    assert res.status_code == 201, f"Pharmacy registration failed: {res.data}"
    pharma_data = res.get_json()
    pharma_token = pharma_data["token"]
    assert pharma_data["user"]["pharmacy"]["pharmacy_name"] == "Apex Care Pharmacy"
    assert pharma_data["user"]["pharmacy"]["license_number"] == "PHARM-LIC-2026-9901"
    print("[OK] Pharmacy registration verified with pharmacy_profile link.")

    # Test 4: Pharmacy Login
    res = client.post("/api/auth/login", json={
        "email": "pharma.central@example.com",
        "password": "PharmacyPass123!"
    })
    assert res.status_code == 200
    login_pharma = res.get_json()
    assert login_pharma["user"]["pharmacy"]["pharmacy_name"] == "Apex Care Pharmacy"
    print("[OK] Pharmacy login returns embedded pharmacy profile.")

    # Test 5: Invalid credentials rejection
    res = client.post("/api/auth/login", json={
        "email": "customer.test@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    print("[OK] Invalid password correctly rejected (401 Unauthorized).")

    # Test 6: Verify /api/auth/me for Customer
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200
    me_cust = res.get_json()
    assert me_cust["user"]["email"] == "customer.test@example.com"
    print("[OK] Protected endpoint /api/auth/me successfully verified with Bearer JWT.")

    # Test 7: Duplicate Email Rejection
    res = client.post("/api/auth/register", json={
        "email": "customer.test@example.com",
        "password": "AnotherPassword!",
        "full_name": "Duplicate User",
        "role": "CUSTOMER",
        "zone": "ZONE_A"
    })
    assert res.status_code == 409
    print("[OK] Duplicate email registration correctly rejected (409 Conflict).")

    # Test 8: Health Check
    res = client.get("/api/health")
    assert res.status_code == 200
    health = res.get_json()
    assert health["broadcast_window_seconds"] == 240
    print(f"[OK] Health check passed (Broadcast window enforced at {health['broadcast_window_seconds']}s).")

    print("\nALL STAGE 2 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
