import openpyxl
from io import BytesIO
from app import create_app
from app.db import get_db

app = create_app()

def create_pharmacy_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pharmacies"
    headers = [
        "Pharmacy Name", "Email", "Password", "Zone",
        "License Number", "Address", "Phone", "Pharmacist Name"
    ]
    ws.append(headers)
    ws.append(["Apex North Dispensary", "apex.north@tapza.com", "ApexPass#123", "ZONE_B", "LIC-ZB-5501", "12 North Sector", "+1-555-4401", "Dr. Nathan Drake"])
    ws.append(["East Care Chemist", "east.care@tapza.com", "EastPass#123", "CENTRAL", "LIC-ZC-6601", "89 Central Way", "+1-555-4402", "Dr. Elena Fisher"])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio

def run_tests():
    print("=== Testing CEO Requirement: Airtight Two-Way Communication & Pharmacy Excel Import ===")
    client = app.test_client()

    # 1. Admin Login & Test Zone-Wise Pharmacy Excel Import
    res_admin = client.post("/api/auth/login", json={"email": "admin@tapza.com", "password": "Admin@123"})
    admin_token = res_admin.get_json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    excel_file = create_pharmacy_excel()
    import_res = client.post(
        "/api/admin/pharmacies/import",
        data={"file": (BytesIO(excel_file.getvalue()), "pharmacies.xlsx")},
        content_type="multipart/form-data",
        headers=admin_headers
    )
    assert import_res.status_code == 200, f"Import failed: {import_res.data}"
    import_stats = import_res.get_json()["stats"]
    assert import_stats["imported"] == 2
    print(f"[OK] Zone-wise Pharmacy Excel bulk import verified: {import_stats['imported']} pharmacies onboarded with credentials.")

    # Verify newly imported pharmacy can log in with imported credentials
    login_imported = client.post("/api/auth/login", json={
        "email": "apex.north@tapza.com",
        "password": "ApexPass#123"
    })
    assert login_imported.status_code == 200
    assert login_imported.get_json()["user"]["pharmacy"]["zone"] == "ZONE_B"
    print("[OK] Imported pharmacy logged in successfully with assigned ZONE_B credentials.")

    # 2. Test Broadcast Instant Notification to ALL Active Pharmacies in Zone
    res_c = client.post("/api/auth/login", json={"email": "customer.test@example.com", "password": "Password123!"})
    cust_token = res_c.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    meds = client.get("/api/medicines?limit=1").get_json()["medicines"]
    med = meds[0]

    # Create order in ZONE_A
    new_o = client.post("/api/orders", json={
        "delivery_address": "77 Sunset Blvd, Zone A",
        "zone": "ZONE_A",
        "items": [{"medicine_id": med["id"], "quantity": 2}]
    }, headers=cust_headers).get_json()["order"]
    oid = new_o["order_id"]

    # Log in both active ZONE_A pharmacies
    p1_headers = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': 'pharma.central@example.com', 'password': 'PharmacyPass123!'}).get_json()['token']}"}
    p2_headers = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'email': 'greenvalley@example.com', 'password': 'Password123!'}).get_json()['token']}"}

    # Verify BOTH pharmacies received persisted NEW_ZONE_BROADCAST alert
    n1 = client.get("/api/notifications", headers=p1_headers).get_json()["notifications"]
    n2 = client.get("/api/notifications", headers=p2_headers).get_json()["notifications"]
    assert any(n["event_type"] == "NEW_ZONE_BROADCAST" and n["reference_id"] == oid for n in n1)
    assert any(n["event_type"] == "NEW_ZONE_BROADCAST" and n["reference_id"] == oid for n in n2)
    print(f"[OK] Two-Way Broadcast verified: Both eligible pharmacies in ZONE_A received instant persisted notifications for Order #{oid}.")

    # 3. Test Rejection Workflow with Alternative Quote Reopening
    item_id = client.get(f"/api/orders/{oid}", headers=cust_headers).get_json()["order"]["items"][0]["id"]

    # Both pharmacies quote
    q1 = client.post("/api/quotes", json={"order_id": oid, "items": [{"order_item_id": item_id, "is_available": True, "unit_selling_price": 79.00}]}, headers=p1_headers).get_json()["quote"]
    q2 = client.post("/api/quotes", json={"order_id": oid, "items": [{"order_item_id": item_id, "is_available": True, "unit_selling_price": 75.00}]}, headers=p2_headers).get_json()["quote"]

    # Customer selects Pharmacy 2 (Green Valley)
    client.post(f"/api/orders/{oid}/select", json={"quote_id": q2["id"]}, headers=cust_headers)

    # Pharmacy 2 rejects fulfillment
    rej_res = client.post(f"/api/pharmacy/orders/{oid}/confirm", json={"action": "REJECT", "rejection_reason": "Out of delivery staff today"}, headers=p2_headers)
    assert rej_res.status_code == 200

    # Verify Order status re-opened to PENDING_SELECTION because Pharmacy 1's quote is still available!
    order_after_rej = client.get(f"/api/orders/{oid}", headers=cust_headers).get_json()["order"]
    assert order_after_rej["status"] == "PENDING_SELECTION"
    print(f"[OK] Rejection Workflow verified: Order #{oid} automatically re-opened to 'PENDING_SELECTION' for alternative quote selection.")

    # Verify Customer received notification with alternative quotes available
    c_notifs = client.get("/api/notifications", headers=cust_headers).get_json()["notifications"]
    assert any(n["event_type"] == "ORDER_REJECTED_ALTERNATIVE_AVAILABLE" and n["reference_id"] == oid for n in c_notifs)
    print("[OK] Customer notified that Pharmacy 2 rejected and alternative quote from Pharmacy 1 is ready to be selected.")

    # Customer can now successfully select Pharmacy 1's alternative quote!
    re_select = client.post(f"/api/orders/{oid}/select", json={"quote_id": q1["id"]}, headers=cust_headers)
    assert re_select.status_code == 200
    assert re_select.get_json()["assignment"]["selected_quote_id"] == q1["id"]
    print(f"[OK] Full Recovery: Customer successfully awarded Order #{oid} to alternative Pharmacy 1!")

    print("\nALL CEO TWO-WAY COMMUNICATION REQUIREMENTS PASSED 100%!")

if __name__ == "__main__":
    run_tests()
