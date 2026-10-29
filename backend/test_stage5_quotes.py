import json
from datetime import datetime, timezone, timedelta
from app import create_app
from app.db import get_db, transaction

app = create_app()

def run_tests():
    print("=== Testing Stage 5: Broadcasts & Pharmacy Quotes ===")
    client = app.test_client()

    # 1. Register a second pharmacy in ZONE_A to test multi-pharmacy competitive quoting
    client.post("/api/auth/register", json={
        "email": "greenvalley@example.com",
        "password": "Password123!",
        "full_name": "Sarah Pharmacist",
        "role": "PHARMACY",
        "phone": "+1-555-0300",
        "zone": "ZONE_A",
        "pharmacy_name": "Green Valley Drugs",
        "license_number": "PHARM-LIC-2026-8802",
        "address": "780 Oak Avenue, Sector 7"
    })

    # Log in Pharmacy 1 (Apex Care)
    res_p1 = client.post("/api/auth/login", json={"email": "pharma.central@example.com", "password": "PharmacyPass123!"})
    token_p1 = res_p1.get_json()["token"]
    headers_p1 = {"Authorization": f"Bearer {token_p1}"}

    # Log in Pharmacy 2 (Green Valley)
    res_p2 = client.post("/api/auth/login", json={"email": "greenvalley@example.com", "password": "Password123!"})
    token_p2 = res_p2.get_json()["token"]
    headers_p2 = {"Authorization": f"Bearer {token_p2}"}
    print("[OK] Both competing pharmacies authenticated in ZONE_A.")

    # 2. Log in Customer and create a fresh active order
    res_cust = client.post("/api/auth/login", json={"email": "customer.test@example.com", "password": "Password123!"})
    cust_token = res_cust.get_json()["token"]
    headers_cust = {"Authorization": f"Bearer {cust_token}"}

    med_res = client.get("/api/medicines?limit=2")
    meds = med_res.get_json()["medicines"]
    med1, med2 = meds[0], meds[1]

    order_res = client.post("/api/orders", json={
        "delivery_address": "88 Elm Street, Zone A",
        "zone": "ZONE_A",
        "items": [
            {"medicine_id": med1["id"], "quantity": 2},
            {"medicine_id": med2["id"], "quantity": 3}
        ]
    }, headers=headers_cust)
    assert order_res.status_code == 201
    order = order_res.get_json()["order"]
    order_id = order["order_id"]
    order_items = client.get(f"/api/orders/{order_id}", headers=headers_cust).get_json()["order"]["items"]
    oi1_id = order_items[0]["id"]
    oi2_id = order_items[1]["id"]
    print(f"[OK] Order #{order_id} created for competitive quoting.")

    # 3. Pharmacy 1 receives broadcast
    b_res = client.get("/api/pharmacy/broadcasts", headers=headers_p1)
    assert b_res.status_code == 200
    broadcasts = b_res.get_json()["broadcasts"]
    assert any(b["order_id"] == order_id for b in broadcasts)
    print(f"[OK] Pharmacy 1 successfully received broadcast for Order #{order_id} (Window active).")

    # 4. Pharmacy 1 submits a FULL Quote (both items available at competitive discount)
    p1_quote_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [
            {"order_item_id": oi1_id, "is_available": True, "unit_selling_price": 80.00},
            {"order_item_id": oi2_id, "is_available": True, "unit_selling_price": 110.00}
        ],
        "notes": "Full stock available, guaranteed 30-min express delivery."
    }, headers=headers_p1)
    assert p1_quote_res.status_code == 201, f"Pharmacy 1 quote failed: {p1_quote_res.data}"
    p1_quote = p1_quote_res.get_json()["quote"]
    assert p1_quote["is_full_fulfillment"] is True
    assert p1_quote["total_quoted_price"] == round((80.00 * 2) + (110.00 * 3), 2)
    print(f"[OK] Pharmacy 1 submitted Full Quote: ${p1_quote['total_quoted_price']} (Full fulfillment).")

    # 5. Pharmacy 2 submits a PARTIAL Quote (Item 1 available, Item 2 unavailable)
    # Strict requirement: Unavailable medicine MUST be charged $0.00
    p2_quote_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [
            {"order_item_id": oi1_id, "is_available": True, "unit_selling_price": 78.00},
            {"order_item_id": oi2_id, "is_available": False, "unit_selling_price": 115.00} # selling price ignored because unavailable
        ],
        "notes": "Item 2 out of stock, Item 1 ready for dispatch."
    }, headers=headers_p2)
    assert p2_quote_res.status_code == 201, f"Pharmacy 2 quote failed: {p2_quote_res.data}"
    p2_quote = p2_quote_res.get_json()["quote"]
    assert p2_quote["is_full_fulfillment"] is False
    assert p2_quote["available_items_count"] == 1
    assert p2_quote["total_items_count"] == 2
    expected_p2_total = round(78.00 * 2, 2)
    assert p2_quote["total_quoted_price"] == expected_p2_total, f"Expected {expected_p2_total}, got {p2_quote['total_quoted_price']}"
    
    # Verify line items: item 2 must have subtotal 0.00
    item2_quoted = next(i for i in p2_quote["items"] if i["order_item_id"] == oi2_id)
    assert item2_quoted["is_available"] == 0
    assert item2_quoted["subtotal_price"] == 0.00
    print(f"[OK] Pharmacy 2 submitted Partial Quote: ${p2_quote['total_quoted_price']} (Unavailable item charged strictly $0.00).")

    # 6. Verify duplicate quote rejection
    dup_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [{"order_item_id": oi1_id, "is_available": True, "unit_selling_price": 75.00}]
    }, headers=headers_p1)
    assert dup_res.status_code == 409
    print("[OK] Duplicate quote from same pharmacy correctly rejected (409 Conflict).")

    # 7. Verify Customer receives notifications for both quotes
    notif_res = client.get("/api/notifications", headers=headers_cust)
    notifs = notif_res.get_json()["notifications"]
    quote_notifs = [n for n in notifs if n["event_type"] == "NEW_QUOTE_RECEIVED"]
    assert len(quote_notifs) >= 2
    print(f"[OK] Customer received {len(quote_notifs)} persistent quote notifications.")

    # 8. Customer queries quotes for comparison
    quotes_res = client.get(f"/api/orders/{order_id}/quotes", headers=headers_cust)
    assert quotes_res.status_code == 200
    all_quotes = quotes_res.get_json()["quotes"]
    assert len(all_quotes) >= 2
    # Verify full fulfillment is sorted first
    assert all_quotes[0]["is_full_fulfillment"] is True
    print(f"[OK] Customer quote comparison verified: {len(all_quotes)} quotes compared with line item breakdowns.")

    # 9. Verify 4-minute window backend expiry enforcement (HTTP 410 Gone)
    # Simulate an expired order in SQLite
    with app.app_context():
        db = get_db()
        with transaction(db):
            past_time = (datetime.now(timezone.utc) - timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S")
            db.execute("UPDATE orders SET broadcast_expires_at = ? WHERE id = ?", (past_time, order_id))

    # Pharmacy attempt to submit quote after expiry must fail with 410 Gone
    expired_attempt = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [{"order_item_id": oi1_id, "is_available": True, "unit_selling_price": 85.00}]
    }, headers=headers_p2)
    assert expired_attempt.status_code == 410, f"Expected 410 Gone for expired window, got {expired_attempt.status_code}"
    print("[OK] Backend strictly rejects quote submission after 4-minute broadcast window (410 Gone).")

    print("\nALL STAGE 5 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
