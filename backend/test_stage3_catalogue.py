import json
from io import BytesIO
import openpyxl
from app import create_app

app = create_app()

def create_test_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catalogue"
    
    headers = [
        "Name", "Generic Name", "Manufacturer", "Category",
        "Dosage Form", "Pack Size", "MRP", "Requires Prescription"
    ]
    ws.append(headers)

    rows = [
        # Valid medicines
        ["Paracetamol 500mg", "Acetaminophen", "GSK", "Analgesic", "Tablet", "10 tabs", 15.50, "No"],
        ["Amoxicillin 500mg", "Amoxicillin Trihydrate", "Novartis", "Antibiotic", "Capsule", "10 caps", 85.00, "Yes"],
        ["Cetirizine 10mg", "Cetirizine HCl", "Dr. Reddy's", "Antihistamine", "Tablet", "10 tabs", 22.00, 0],
        ["Metformin 500mg", "Metformin HCl", "Sun Pharma", "Antidiabetic", "Tablet", "20 tabs", 45.00, 1],
        ["Atorvastatin 20mg", "Atorvastatin", "Cipla", "Cardiovascular", "Tablet", "15 tabs", 120.00, "Yes"],
        
        # Invalid row 1: Empty name
        ["", "Unknown", "Pharma", "General", "Tablet", "10 tabs", 10.00, "No"],
        
        # Invalid row 2: Negative MRP
        ["Negative Price Med", "Invalid", "Pharma", "General", "Tablet", "10 tabs", -50.00, "No"],
        
        # Invalid row 3: Non-numeric MRP
        ["Bad Price Med", "Invalid", "Pharma", "General", "Tablet", "10 tabs", "FREE", "No"]
    ]
    for r in rows:
        ws.append(r)

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio

def run_tests():
    print("=== Testing Stage 3: Medicine Catalogue & Validated Excel Import ===")
    client = app.test_client()

    # 1. Log in as Admin
    login_res = client.post("/api/auth/login", json={
        "email": "admin@tapza.com",
        "password": "Admin@123"
    })
    assert login_res.status_code == 200
    admin_token = login_res.get_json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[OK] Admin token obtained.")

    # 2. Log in as Customer to test RBAC rejection on admin routes
    cust_res = client.post("/api/auth/login", json={
        "email": "customer.test@example.com",
        "password": "Password123!"
    })
    assert cust_res.status_code == 200
    cust_token = cust_res.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 3. Test Unauthorized Import Attempt by Customer (Should fail 403)
    excel_stream = create_test_excel()
    data = {"file": (BytesIO(excel_stream.getvalue()), "catalogue.xlsx")}
    res = client.post("/api/medicines/import", data=data, content_type="multipart/form-data", headers=cust_headers)
    assert res.status_code == 403, f"Customer should not be able to import catalogue: {res.status_code}"
    print("[OK] RBAC verified: Customer denied access to catalogue import (403 Forbidden).")

    # 4. Test Validated Excel Import by Admin
    data = {"file": (BytesIO(excel_stream.getvalue()), "catalogue.xlsx")}
    res = client.post("/api/medicines/import", data=data, content_type="multipart/form-data", headers=admin_headers)
    assert res.status_code == 200, f"Import failed: {res.data}"
    import_stats = res.get_json()["stats"]
    print(f"Import stats received: {import_stats}")
    assert import_stats["imported"] >= 5, "Expected at least 5 valid medicines imported"
    assert import_stats["rejected_count"] == 3, f"Expected 3 invalid rows rejected, got {import_stats['rejected_count']}"
    print(f"[OK] Validated Excel import processed successfully: {import_stats['imported']} imported, {import_stats['rejected_count']} correctly rejected with validation error logs.")

    # 5. Test Search & Listing
    res = client.get("/api/medicines?search=paracetamol")
    assert res.status_code == 200
    search_data = res.get_json()
    assert len(search_data["medicines"]) >= 1
    med = search_data["medicines"][0]
    assert "Paracetamol" in med["name"]
    assert med["mrp"] == 15.50
    print(f"[OK] Search verified: Found '{med['name']}' with MRP preserved at {med['mrp']}.")

    # 6. Test Category Filter
    res = client.get("/api/medicines?category=Antibiotic")
    assert res.status_code == 200
    cat_data = res.get_json()
    assert len(cat_data["medicines"]) >= 1
    assert cat_data["medicines"][0]["category"] == "Antibiotic"
    print(f"[OK] Category filter verified: Found {len(cat_data['medicines'])} Antibiotic item(s).")

    # 7. Test Categories Endpoint
    res = client.get("/api/medicines/categories")
    assert res.status_code == 200
    categories = res.get_json()["categories"]
    assert "Antibiotic" in categories
    assert "Analgesic" in categories
    print(f"[OK] Categories listed: {', '.join(categories)}")

    # 8. Test Single Medicine Creation by Admin
    res = client.post("/api/medicines", json={
        "name": "Azithromycin 500mg",
        "generic_name": "Azithromycin",
        "manufacturer": "Pfizer",
        "category": "Antibiotic",
        "dosage_form": "Tablet",
        "pack_size": "3 tablets",
        "mrp": 95.00,
        "requires_prescription": True
    }, headers=admin_headers)
    assert res.status_code == 201
    created_med = res.get_json()["medicine"]
    created_id = created_med["id"]
    print(f"[OK] Admin created medicine '{created_med['name']}' (ID: {created_id}).")

    # 9. Test Single Medicine Update by Admin
    res = client.put(f"/api/medicines/{created_id}", json={
        "name": "Azithromycin 500mg (Updated)",
        "mrp": 98.00,
        "category": "Antibiotic"
    }, headers=admin_headers)
    assert res.status_code == 200
    print("[OK] Admin updated medicine details.")

    # 10. Test Excel Template Download
    res = client.get("/api/medicines/template")
    assert res.status_code == 200
    assert "spreadsheetml.sheet" in res.content_type
    print(f"[OK] Excel starter template download verified ({len(res.data)} bytes).")

    print("\nALL STAGE 3 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
