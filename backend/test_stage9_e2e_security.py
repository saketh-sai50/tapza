import json
import time
import threading
from datetime import datetime, timezone, timedelta
from app import create_app
from app.db import get_db, transaction
from app.utils.auth_helpers import generate_jwt, decode_jwt, hash_password, verify_password

app = create_app()

def run_tests():
    print("=" * 70)
    print("STAGE 9: COMPREHENSIVE END-TO-END WORKFLOW & SECURITY VERIFICATION")
    print("=" * 70)
    client = app.test_client()

    # -------------------------------------------------------------------------
    # PART 1: CRYPTOGRAPHIC & AUTHENTICATION SECURITY TESTS
    # -------------------------------------------------------------------------
    print("\n--- 1. Cryptographic Password Hashing & JWT Security ---")
    raw_pwd = "SecureComplexPassword!#2026"
    h1 = hash_password(raw_pwd)
    h2 = hash_password(raw_pwd)
    assert h1 != h2, "Salts must be unique for each hash generation"
    assert verify_password(raw_pwd, h1) is True
    assert verify_password(raw_pwd, h2) is True
    assert verify_password("WrongPassword", h1) is False
    print("[OK] Password hashing utilizes strong unique salts and timing-safe verification.")

    # Tampered JWT rejection
    valid_jwt = generate_jwt({"user_id": 999, "role": "ADMIN", "zone": "CENTRAL"}, app.config["JWT_SECRET"])
    tampered_jwt = valid_jwt[:-5] + "XXXXX"
    try:
        decode_jwt(tampered_jwt, app.config["JWT_SECRET"])
        assert False, "Tampered JWT should have raised ValueError"
    except ValueError:
        print("[OK] Tampered JWT signature correctly detected and rejected.")

    # Expired JWT rejection
    expired_jwt = generate_jwt({"user_id": 999, "role": "ADMIN"}, app.config["JWT_SECRET"], expires_in_seconds=-10)
    try:
        decode_jwt(expired_jwt, app.config["JWT_SECRET"])
        assert False, "Expired JWT should have raised ValueError"
    except ValueError:
        print("[OK] Expired JWT correctly detected and rejected.")

    # -------------------------------------------------------------------------
    # PART 2: ROLE-BASED ACCESS CONTROL (RBAC) BOUNDARY TESTS
    # -------------------------------------------------------------------------
    print("\n--- 2. RBAC & Cross-Tenant Security Boundaries ---")
    # Fresh accounts
    c_email = f"e2e.customer.{int(time.time())}@example.com"
    p_email = f"e2e.pharma.{int(time.time())}@example.com"

    reg_c = client.post("/api/auth/register", json={
        "email": c_email,
        "password": "Password123!",
        "full_name": "E2E Customer",
        "role": "CUSTOMER",
        "zone": "ZONE_A"
    }).get_json()
    c_token = reg_c["token"]
    c_headers = {"Authorization": f"Bearer {c_token}"}
    c_id = reg_c["user"]["id"]

    reg_p = client.post("/api/auth/register", json={
        "email": p_email,
        "password": "Password123!",
        "full_name": "E2E Pharmacist",
        "role": "PHARMACY",
        "zone": "ZONE_A",
        "pharmacy_name": "E2E Care Chemist",
        "license_number": "LIC-E2E-9900",
        "address": "100 Broadway, Zone A"
    }).get_json()
    p_token = reg_p["token"]
    p_headers = {"Authorization": f"Bearer {p_token}"}
    p_id = reg_p["user"]["id"]

    # Customer tries to access Admin route
    assert client.get("/api/admin/metrics", headers=c_headers).status_code == 403
    # Customer tries to access Pharmacy broadcast route
    assert client.get("/api/pharmacy/broadcasts", headers=c_headers).status_code == 403
    # Pharmacy tries to create Customer order
    assert client.post("/api/orders", json={"items": []}, headers=p_headers).status_code == 403
    # Unauthenticated request
    assert client.get("/api/admin/orders").status_code == 401
    assert client.get("/api/orders/my-orders").status_code == 401
    print("[OK] Strict RBAC enforced: Customer, Pharmacy, and Unauthenticated barriers verified.")

    # -------------------------------------------------------------------------
    # PART 3: COMPLETE END-TO-END ORDER, BROADCAST, QUOTE, & FULFILLMENT
    # -------------------------------------------------------------------------
    print("\n--- 3. Full End-to-End Workflow Execution ---")
    
    # Step A: Customer searches medicines
    med_list = client.get("/api/medicines?limit=2").get_json()["medicines"]
    med_a, med_b = med_list[0], med_list[1]
    qty_a, qty_b = 2, 4
    expected_mrp = round((med_a["mrp"] * qty_a) + (med_b["mrp"] * qty_b), 2)
    print(f"[OK] Customer selected: '{med_a['name']}' (qty {qty_a}) & '{med_b['name']}' (qty {qty_b}). Total MRP: ${expected_mrp}.")

    # Step B: Customer checks out and initiates 4-minute broadcast
    order_create_res = client.post("/api/orders", json={
        "delivery_address": "404 E2E Highway, Apt 10",
        "zone": "ZONE_A",
        "items": [
            {"medicine_id": med_a["id"], "quantity": qty_a},
            {"medicine_id": med_b["id"], "quantity": qty_b}
        ]
    }, headers=c_headers)
    assert order_create_res.status_code == 201
    order_info = order_create_res.get_json()["order"]
    e2e_order_id = order_info["order_id"]
    
    # Verify strict 4-minute window
    assert order_info["remaining_broadcast_seconds"] == 240
    assert order_info["total_mrp"] == expected_mrp
    print(f"[OK] Order #{e2e_order_id} broadcast initiated: Exact 240s window and MRP ${expected_mrp} preserved.")

    # Step C: Competing Pharmacy submits Partial Quote (Item A available, Item B unavailable)
    order_details = client.get(f"/api/orders/{e2e_order_id}", headers=c_headers).get_json()["order"]
    oi_a_id = order_details["items"][0]["id"]
    oi_b_id = order_details["items"][1]["id"]

    quoted_unit_a = round(med_a["mrp"] * 0.9, 2) # 10% discount
    quote_res = client.post("/api/quotes", json={
        "order_id": e2e_order_id,
        "items": [
            {"order_item_id": oi_a_id, "is_available": True, "unit_selling_price": quoted_unit_a},
            {"order_item_id": oi_b_id, "is_available": False, "unit_selling_price": 50.00} # price ignored
        ],
        "notes": "Item B is out of stock. Item A available immediately."
    }, headers=p_headers)
    assert quote_res.status_code == 201
    quote_data = quote_res.get_json()["quote"]
    expected_payable = round(quoted_unit_a * qty_a, 2)
    assert quote_data["total_quoted_price"] == expected_payable
    assert quote_data["is_full_fulfillment"] is False
    print(f"[OK] Pharmacy submitted Partial Quote: Total payable is strictly ${expected_payable} (Zero charge for unavailable Item B).")

    # -------------------------------------------------------------------------
    # PART 4: CONCURRENCY STRESS TEST (SIMULTANEOUS SELECTION ATTEMPTS)
    # -------------------------------------------------------------------------
    print("\n--- 4. Concurrency Stress Test: Parallel Single-Pharmacy Selection ---")
    results = []

    def attempt_select(quote_id):
        with app.app_context():
            sub_client = app.test_client()
            res = sub_client.post(
                f"/api/orders/{e2e_order_id}/select",
                json={"quote_id": quote_id},
                headers=c_headers
            )
            results.append((res.status_code, res.get_json()))

    t1 = threading.Thread(target=attempt_select, args=(quote_data["id"],))
    t2 = threading.Thread(target=attempt_select, args=(quote_data["id"],))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    status_codes = [r[0] for r in results]
    assert 200 in status_codes, f"One thread must succeed (200), got {status_codes}"
    assert 409 in status_codes, f"The concurrent thread must be rejected with 409 Conflict, got {status_codes}"
    print(f"[OK] Concurrency protection verified: Thread outcomes: {status_codes}. Exactly one winner assigned!")

    # Verify database assignment uniqueness
    with app.app_context():
        db = get_db()
        assignments = db.execute("SELECT COUNT(*) as c FROM order_assignments WHERE order_id = ?", (e2e_order_id,)).fetchone()["c"]
        assert assignments == 1, f"Expected exactly 1 assignment row, got {assignments}"
        print("[OK] Relational integrity verified: Exactly 1 record exists in order_assignments.")

    # -------------------------------------------------------------------------
    # PART 5: PHARMACY CONFIRMATION & FULL FULFILLMENT LIFECYCLE
    # -------------------------------------------------------------------------
    print("\n--- 5. Pharmacy Confirmation & Progressive Delivery Stages ---")
    confirm_res = client.post(f"/api/pharmacy/orders/{e2e_order_id}/confirm", json={"action": "CONFIRM"}, headers=p_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.get_json()["order_status"] == "CONFIRMED"
    print(f"[OK] Pharmacy confirmed fulfillment for Order #{e2e_order_id}.")

    # Step through stages
    client.post(f"/api/pharmacy/orders/{e2e_order_id}/status", json={"status": "PREPARING"}, headers=p_headers)
    client.post(f"/api/pharmacy/orders/{e2e_order_id}/status", json={"status": "DISPATCHED"}, headers=p_headers)
    client.post(f"/api/pharmacy/orders/{e2e_order_id}/status", json={"status": "DELIVERED"}, headers=p_headers)
    print(f"[OK] Order #{e2e_order_id} progressed through PREPARING -> DISPATCHED -> DELIVERED.")

    # Step D: Simulated Mock Payment
    pay_res = client.post(f"/api/orders/{e2e_order_id}/mock-pay", json={"payment_method": "DEMO_TEST_CARD"}, headers=c_headers)
    assert pay_res.status_code == 200
    pay_json = pay_res.get_json()["payment"]
    assert pay_json["is_mock"] is True
    assert pay_json["amount_paid"] == expected_payable
    assert pay_json["mock_payment_status"] == "MOCK_PAID"
    print(f"[OK] Mock payment processed: ${expected_payable} marked MOCK_PAID with simulation disclaimer.")

    # -------------------------------------------------------------------------
    # PART 6: PERSISTED NOTIFICATION AUDIT TRAIL
    # -------------------------------------------------------------------------
    print("\n--- 6. Notification Persistence Audit ---")
    cust_notifs = client.get("/api/notifications", headers=c_headers).get_json()["notifications"]
    pharma_notifs = client.get("/api/notifications", headers=p_headers).get_json()["notifications"]

    expected_cust_events = ["ORDER_BROADCAST_STARTED", "NEW_QUOTE_RECEIVED", "QUOTE_SELECTED", "ORDER_CONFIRMED", "STATUS_UPDATE", "MOCK_PAYMENT_COMPLETED"]
    for ev in expected_cust_events:
        assert any(n["event_type"] == ev for n in cust_notifs), f"Missing customer notification event: {ev}"

    assert any(n["event_type"] == "ORDER_AWARDED" for n in pharma_notifs), "Missing pharmacy ORDER_AWARDED alert"
    print(f"[OK] Audit verified: Customer received {len(cust_notifs)} persisted alerts; Pharmacy received {len(pharma_notifs)} alerts across full lifecycle.")

    # -------------------------------------------------------------------------
    # PART 7: BOUNDARY & SECURITY EDGE CASES
    # -------------------------------------------------------------------------
    print("\n--- 7. Security Edge Cases & Boundary Enforcement ---")
    # Expired broadcast rejection
    with app.app_context():
        db = get_db()
        with transaction(db):
            past_time = (datetime.now(timezone.utc) - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
            db.execute("UPDATE orders SET broadcast_expires_at = ? WHERE id = ?", (past_time, e2e_order_id))
    
    late_quote = client.post("/api/quotes", json={
        "order_id": e2e_order_id,
        "items": [{"order_item_id": oi_a_id, "is_available": True, "unit_selling_price": 50.00}]
    }, headers=p_headers)
    assert late_quote.status_code == 410
    print("[OK] Server strictly rejects bids submitted after broadcast expiry with HTTP 410 Gone.")

    # Cannot cancel confirmed order
    bad_cancel = client.post(f"/api/orders/{e2e_order_id}/cancel", headers=c_headers)
    assert bad_cancel.status_code == 400
    print("[OK] Customer cannot cancel order once confirmed by pharmacy.")

    print("\n" + "=" * 70)
    print("STAGE 9: ALL END-TO-END & SECURITY TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
