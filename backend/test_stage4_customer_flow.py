from datetime import datetime, timezone
from app import create_app
from app.db import get_db

app = create_app()

def run_tests():
    print("=== Testing Stage 4: Customer Catalogue, Cart, & Checkout Broadcast ===")
    client = app.test_client()

    # 1. Login as Customer
    cust_res = client.post("/api/auth/login", json={
        "email": "customer.test@example.com",
        "password": "Password123!"
    })
    assert cust_res.status_code == 200
    cust_token = cust_res.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("[OK] Customer authenticated.")

    # 2. Query Medicines to add to cart
    med_res = client.get("/api/medicines?limit=5")
    assert med_res.status_code == 200
    meds = med_res.get_json()["medicines"]
    assert len(meds) >= 2
    med1 = meds[0]
    med2 = meds[1]
    print(f"[OK] Selected cart medicines: '{med1['name']}' (MRP ${med1['mrp']}) and '{med2['name']}' (MRP ${med2['mrp']}).")

    # 3. Place Order & Start 4-Minute Broadcast
    order_payload = {
        "delivery_address": "742 Evergreen Terrace, Sector 7",
        "zone": "ZONE_A",
        "items": [
            {"medicine_id": med1["id"], "quantity": 2},
            {"medicine_id": med2["id"], "quantity": 3}
        ]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=cust_headers)
    assert create_res.status_code == 201, f"Order creation failed: {create_res.data}"
    order_data = create_res.get_json()["order"]
    order_id = order_data["order_id"]

    expected_total_mrp = round((med1["mrp"] * 2) + (med2["mrp"] * 3), 2)
    assert order_data["status"] == "BROADCASTING"
    assert order_data["total_mrp"] == expected_total_mrp
    print(f"[OK] Order #{order_id} created with status 'BROADCASTING' and Total MRP ${order_data['total_mrp']}.")

    # 4. Strict Backend 4-Minute Window Verification
    started_dt = datetime.strptime(order_data["broadcast_started_at"], "%Y-%m-%d %H:%M:%S")
    expires_dt = datetime.strptime(order_data["broadcast_expires_at"], "%Y-%m-%d %H:%M:%S")
    duration_seconds = int((expires_dt - started_dt).total_seconds())
    assert duration_seconds == 240, f"Broadcast window must be exactly 240s, got {duration_seconds}s"
    print(f"[OK] Broadcast window duration strictly enforced at exactly {duration_seconds} seconds (4 minutes).")

    # 5. Verify Notification Persistence
    notif_res = client.get("/api/notifications", headers=cust_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.get_json()["notifications"]
    assert len(notifs) >= 1
    recent_notif = next((n for n in notifs if n["reference_id"] == order_id and n["event_type"] == "ORDER_BROADCAST_STARTED"), notifs[0])
    assert recent_notif["event_type"] == "ORDER_BROADCAST_STARTED"
    assert recent_notif["reference_id"] == order_id
    print(f"[OK] Persisted customer notification verified: '{recent_notif['title']}'.")

    # 6. Verify Customer Orders List
    list_res = client.get("/api/orders/my-orders", headers=cust_headers)
    assert list_res.status_code == 200
    my_orders = list_res.get_json()["orders"]
    assert any(o["id"] == order_id for o in my_orders)
    found_order = next(o for o in my_orders if o["id"] == order_id)
    assert found_order["remaining_broadcast_seconds"] > 0
    print(f"[OK] My Orders list verified: Order #{order_id} active with {found_order['remaining_broadcast_seconds']}s remaining.")

    # 7. Verify Order Details Endpoint
    detail_res = client.get(f"/api/orders/{order_id}", headers=cust_headers)
    assert detail_res.status_code == 200
    detail = detail_res.get_json()["order"]
    assert len(detail["items"]) == 2
    assert detail["items"][0]["unit_mrp"] == med1["mrp"]
    print(f"[OK] Order details verified: Line items preserve MRP (${detail['items'][0]['unit_mrp']}).")

    # 8. Test Order Cancellation
    cancel_res = client.post(f"/api/orders/{order_id}/cancel", headers=cust_headers)
    assert cancel_res.status_code == 200
    detail_after_cancel = client.get(f"/api/orders/{order_id}", headers=cust_headers).get_json()["order"]
    assert detail_after_cancel["status"] == "CANCELLED"
    print("[OK] Order cancellation verified: Status transitioned to 'CANCELLED'.")

    # 9. Create another active order for Stage 5 quoting
    order2_res = client.post("/api/orders", json=order_payload, headers=cust_headers)
    assert order2_res.status_code == 201
    order2_id = order2_res.get_json()["order"]["order_id"]
    print(f"[OK] New active order #{order2_id} created in 'BROADCASTING' state ready for pharmacy quotes in Stage 5.")

    print("\nALL STAGE 4 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
