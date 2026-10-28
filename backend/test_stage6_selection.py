import json
from app import create_app
from app.db import get_db

app = create_app()

def run_tests():
    print("=== Testing Stage 6: Quote Selection, Partial Fulfillment, & Mock Payment ===")
    client = app.test_client()

    # 1. Customer Login
    res_c = client.post("/api/auth/login", json={"email": "customer.test@example.com", "password": "Password123!"})
    cust_token = res_c.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 2. Pharmacy 1 & 2 Logins
    res_p1 = client.post("/api/auth/login", json={"email": "pharma.central@example.com", "password": "PharmacyPass123!"})
    headers_p1 = {"Authorization": f"Bearer {res_p1.get_json()['token']}"}

    res_p2 = client.post("/api/auth/login", json={"email": "greenvalley@example.com", "password": "Password123!"})
    headers_p2 = {"Authorization": f"Bearer {res_p2.get_json()['token']}"}
    p2_id = res_p2.get_json()["user"]["id"]

    # 3. Create fresh Order for selection test
    meds = client.get("/api/medicines?limit=2").get_json()["medicines"]
    med1, med2 = meds[0], meds[1]

    order_res = client.post("/api/orders", json={
        "delivery_address": "500 Selection Way, Zone A",
        "zone": "ZONE_A",
        "items": [
            {"medicine_id": med1["id"], "quantity": 2},
            {"medicine_id": med2["id"], "quantity": 3}
        ]
    }, headers=cust_headers)
    order_id = order_res.get_json()["order"]["order_id"]
    order_items = client.get(f"/api/orders/{order_id}", headers=cust_headers).get_json()["order"]["items"]
    oi1_id = order_items[0]["id"]
    oi2_id = order_items[1]["id"]
    print(f"[OK] Order #{order_id} created for selection testing.")

    # 4. Pharmacy 1 submits Full Quote ($490.00)
    q1_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [
            {"order_item_id": oi1_id, "is_available": True, "unit_selling_price": 80.00},
            {"order_item_id": oi2_id, "is_available": True, "unit_selling_price": 110.00}
        ]
    }, headers=headers_p1)
    q1_id = q1_res.get_json()["quote"]["id"]

    # 5. Pharmacy 2 submits Partial Quote ($156.00) with Item 2 UNAVAILABLE
    q2_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [
            {"order_item_id": oi1_id, "is_available": True, "unit_selling_price": 78.00},
            {"order_item_id": oi2_id, "is_available": False, "unit_selling_price": 0.00}
        ]
    }, headers=headers_p2)
    q2_id = q2_res.get_json()["quote"]["id"]
    print(f"[OK] Quotes submitted: Q#{q1_id} (Full, $490.00) and Q#{q2_id} (Partial, $156.00).")

    # 6. Customer selects Pharmacy 2's Partial Quote
    sel_res = client.post(f"/api/orders/{order_id}/select", json={"quote_id": q2_id}, headers=cust_headers)
    assert sel_res.status_code == 200, f"Selection failed: {sel_res.data}"
    assignment = sel_res.get_json()["assignment"]
    assert assignment["selected_quote_id"] == q2_id
    assert assignment["final_payable_amount"] == 156.00
    print(f"[OK] Customer successfully selected Pharmacy 2 Quote #{q2_id}. Final amount locked to ${assignment['final_payable_amount']}.")

    # 7. Verify Database State
    with app.app_context():
        db = get_db()
        q2_row = db.execute("SELECT status FROM quotes WHERE id = ?", (q2_id,)).fetchone()
        q1_row = db.execute("SELECT status FROM quotes WHERE id = ?", (q1_id,)).fetchone()
        order_row = db.execute("SELECT status, final_amount FROM orders WHERE id = ?", (order_id,)).fetchone()
        assign_row = db.execute("SELECT pharmacy_id, confirmation_status FROM order_assignments WHERE order_id = ?", (order_id,)).fetchone()

        assert q2_row["status"] == "SELECTED", f"Expected SELECTED, got {q2_row['status']}"
        assert q1_row["status"] == "REJECTED", f"Expected REJECTED, got {q1_row['status']}"
        assert order_row["status"] == "CONFIRMED_PENDING_PHARMACY"
        assert order_row["final_amount"] == 156.00
        assert assign_row["pharmacy_id"] == p2_id
        assert assign_row["confirmation_status"] == "PENDING"
        print("[OK] Database transaction verified: Winner marked SELECTED, competitor REJECTED, assignment recorded.")

    # 8. CRITICAL CONCURRENCY PROTECTION TEST: Double-Selection Conflict (409 Conflict)
    dup_sel_res = client.post(f"/api/orders/{order_id}/select", json={"quote_id": q1_id}, headers=cust_headers)
    assert dup_sel_res.status_code == 409, f"Expected 409 Conflict, got {dup_sel_res.status_code}"
    print("[OK] Concurrency protection verified: Second selection attempt rejected with 409 Conflict.")

    # 9. Verify Notifications
    p2_notifs = client.get("/api/notifications", headers=headers_p2).get_json()["notifications"]
    assert any(n["event_type"] == "ORDER_AWARDED" and n["reference_id"] == order_id for n in p2_notifs)
    print("[OK] Winning Pharmacy received persistent 'ORDER_AWARDED' notification.")

    # 10. Test Mock Simulated Payment
    pay_res = client.post(f"/api/orders/{order_id}/mock-pay", json={"payment_method": "DEMO_TEST_CARD"}, headers=cust_headers)
    assert pay_res.status_code == 200
    pay_data = pay_res.get_json()["payment"]
    assert pay_data["is_mock"] is True
    assert pay_data["mock_payment_status"] == "MOCK_PAID"
    assert pay_data["amount_paid"] == 156.00
    print(f"[OK] Mock payment simulation verified: ${pay_data['amount_paid']} marked MOCK_PAID with explicit simulation disclaimer.")

    print("\nALL STAGE 6 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
