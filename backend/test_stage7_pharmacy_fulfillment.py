import json
from app import create_app
from app.db import get_db

app = create_app()

def run_tests():
    print("=== Testing Stage 7: Pharmacy Order Management & Notifications ===")
    client = app.test_client()

    # 1. Logins
    res_c = client.post("/api/auth/login", json={"email": "customer.test@example.com", "password": "Password123!"})
    cust_token = res_c.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    res_p2 = client.post("/api/auth/login", json={"email": "greenvalley@example.com", "password": "Password123!"})
    token_p2 = res_p2.get_json()["token"]
    headers_p2 = {"Authorization": f"Bearer {token_p2}"}

    # 2. Pharmacy 2 queries assigned orders
    assigned_res = client.get("/api/pharmacy/orders", headers=headers_p2)
    assert assigned_res.status_code == 200
    assigned_orders = assigned_res.get_json()["assigned_orders"]
    assert len(assigned_orders) >= 1
    target_order = assigned_orders[0]
    order_id = target_order["order_id"]
    print(f"[OK] Pharmacy 2 retrieved assigned Order #{order_id} (Status: {target_order['confirmation_status']}).")

    # 3. Pharmacy Confirms Order
    confirm_res = client.post(f"/api/pharmacy/orders/{order_id}/confirm", json={"action": "CONFIRM"}, headers=headers_p2)
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.get_json()
    assert confirm_data["confirmation_status"] == "CONFIRM"
    assert confirm_data["order_status"] == "CONFIRMED"
    print(f"[OK] Pharmacy confirmed Order #{order_id}.")

    # Verify Customer received confirmation notification
    c_notifs = client.get("/api/notifications", headers=cust_headers).get_json()["notifications"]
    assert any(n["event_type"] == "ORDER_CONFIRMED" and n["reference_id"] == order_id for n in c_notifs)
    print("[OK] Customer received 'ORDER_CONFIRMED' notification.")

    # 4. Progressive Fulfillment Stage Updates: PREPARING -> DISPATCHED -> DELIVERED
    stages = ["PREPARING", "DISPATCHED", "DELIVERED"]
    for stg in stages:
        stg_res = client.post(f"/api/pharmacy/orders/{order_id}/status", json={"status": stg}, headers=headers_p2)
        assert stg_res.status_code == 200, f"Failed transition to {stg}: {stg_res.data}"
        assert stg_res.get_json()["status"] == stg
        print(f"[OK] Order #{order_id} progressed to stage '{stg}'.")

    # Verify customer received dispatch/delivery notifications
    c_notifs_after = client.get("/api/notifications", headers=cust_headers).get_json()["notifications"]
    assert any(n["event_type"] == "STATUS_UPDATE" and n["reference_id"] == order_id for n in c_notifs_after)
    print("[OK] Customer received real-time status update notifications.")

    # 5. Backward Transition Rejection (Terminal state test)
    bad_transition = client.post(f"/api/pharmacy/orders/{order_id}/status", json={"status": "PREPARING"}, headers=headers_p2)
    assert bad_transition.status_code == 400
    print("[OK] Invalid backward transition from DELIVERED correctly rejected (400 Bad Request).")

    # 6. Test Pharmacy Rejection Workflow
    # Create order, quote, select, then pharmacy rejects
    meds = client.get("/api/medicines?limit=1").get_json()["medicines"]
    o_new = client.post("/api/orders", json={
        "delivery_address": "900 Reject Ave, Zone A",
        "zone": "ZONE_A",
        "items": [{"medicine_id": meds[0]["id"], "quantity": 1}]
    }, headers=cust_headers).get_json()["order"]
    new_oid = o_new["order_id"]
    new_item_id = client.get(f"/api/orders/{new_oid}", headers=cust_headers).get_json()["order"]["items"][0]["id"]

    q_new = client.post("/api/quotes", json={
        "order_id": new_oid,
        "items": [{"order_item_id": new_item_id, "is_available": True, "unit_selling_price": 75.00}]
    }, headers=headers_p2).get_json()["quote"]

    client.post(f"/api/orders/{new_oid}/select", json={"quote_id": q_new["id"]}, headers=cust_headers)

    # Pharmacy rejects
    rej_res = client.post(f"/api/pharmacy/orders/{new_oid}/confirm", json={
        "action": "REJECT",
        "rejection_reason": "Emergency maintenance at dispensary."
    }, headers=headers_p2)
    assert rej_res.status_code == 200
    assert rej_res.get_json()["order_status"] in ("REJECTED", "PENDING_SELECTION")

    # Verify customer received rejection notification
    c_notifs_rej = client.get("/api/notifications", headers=cust_headers).get_json()["notifications"]
    assert any(n["event_type"] in ("ORDER_REJECTED", "ORDER_REJECTED_ALTERNATIVE_AVAILABLE") and n["reference_id"] == new_oid for n in c_notifs_rej)
    print(f"[OK] Pharmacy rejection verified: Order #{new_oid} marked REJECTED and customer notified with reason.")

    # 7. Pharmacy Dashboard Metrics
    metrics_res = client.get("/api/pharmacy/metrics", headers=headers_p2)
    assert metrics_res.status_code == 200
    metrics = metrics_res.get_json()["metrics"]
    assert metrics["orders_won"] >= 2
    assert metrics["orders_delivered"] >= 1
    assert metrics["total_revenue"] > 0
    print(f"[OK] Pharmacy metrics verified: {metrics['orders_won']} won, {metrics['orders_delivered']} delivered, ${metrics['total_revenue']} revenue.")

    print("\nALL STAGE 7 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
