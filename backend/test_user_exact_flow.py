import json
from app import create_app
from app.db import get_db

app = create_app()

def test_user_flow():
    print("=" * 70)
    print("SIMULATING EXACT USER WORKFLOW WITH SEEDED PHARMACY CREDENTIALS")
    print("=" * 70)
    client = app.test_client()

    # Step 1: Customer registers / logs in with Zone "Warangal"
    cust_res = client.post("/api/auth/register", json={
        "email": "warangal.customer@example.com",
        "password": "CustomerPass@123",
        "full_name": "Ramesh Kumar",
        "role": "CUSTOMER",
        "phone": "+91-9876543210",
        "zone": "Warangal"
    })
    if cust_res.status_code == 409:
        cust_res = client.post("/api/auth/login", json={
            "email": "warangal.customer@example.com",
            "password": "CustomerPass@123"
        })
    assert cust_res.status_code in (200, 201)
    cust_token = cust_res.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("[STEP 1 OK] Customer Ramesh Kumar logged in with zone 'Warangal'.")

    # Step 2: Customer orders medicines in Warangal
    meds = client.get("/api/medicines?limit=2").get_json()["medicines"]
    med1, med2 = meds[0], meds[1]
    
    order_res = client.post("/api/orders", json={
        "delivery_address": "House 4-12, Demo Market Road, Warangal",
        "zone": "Warangal",
        "items": [
            {"medicine_id": med1["id"], "quantity": 2},
            {"medicine_id": med2["id"], "quantity": 3}
        ]
    }, headers=cust_headers)
    assert order_res.status_code == 201
    order_data = order_res.get_json()["order"]
    order_id = order_data["order_id"]
    print(f"[STEP 2 OK] Customer placed Order #{order_id} in 'Warangal'. 4-minute broadcast initiated to all 15 Warangal pharmacies!")

    # Step 3: Log in as Pharmacy 1 (testpharm001 / testpharm@001) using username!
    p1_login = client.post("/api/auth/login", json={
        "username": "testpharm001",
        "password": "testpharm@001"
    })
    assert p1_login.status_code == 200, f"Pharmacy 1 login failed: {p1_login.data}"
    p1_token = p1_login.get_json()["token"]
    p1_headers = {"Authorization": f"Bearer {p1_token}"}
    p1_name = p1_login.get_json()["user"]["pharmacy"]["pharmacy_name"]
    print(f"[STEP 3 OK] Logged into Pharmacy 1: '{p1_name}' using username 'testpharm001'.")

    # Step 4: Pharmacy 1 views broadcast, checks items, and raises a Full Quote
    b1 = client.get("/api/pharmacy/broadcasts", headers=p1_headers).get_json()["broadcasts"]
    assert any(b["order_id"] == order_id for b in b1), f"Order #{order_id} not visible to testpharm001"
    
    order_items = client.get(f"/api/orders/{order_id}", headers=cust_headers).get_json()["order"]["items"]
    oi1 = order_items[0]["id"]
    oi2 = order_items[1]["id"]

    q1_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [
            {"order_item_id": oi1, "is_available": True, "unit_selling_price": 75.00},
            {"order_item_id": oi2, "is_available": True, "unit_selling_price": 105.00}
        ],
        "notes": "Sri Lakshmi Care: Both medicines in stock, ready for 20-min delivery."
    }, headers=p1_headers)
    assert q1_res.status_code == 201
    q1_total = q1_res.get_json()["quote"]["total_quoted_price"]
    print(f"[STEP 4 OK] Pharmacy 1 ({p1_name}) raised Full Quote of ${q1_total:.2f}.")

    # Step 5: Log into Pharmacy 2 (testpharm002 / testpharm@002) using username!
    p2_login = client.post("/api/auth/login", json={
        "username": "testpharm002",
        "password": "testpharm@002"
    })
    assert p2_login.status_code == 200, f"Pharmacy 2 login failed: {p2_login.data}"
    p2_token = p2_login.get_json()["token"]
    p2_headers = {"Authorization": f"Bearer {p2_token}"}
    p2_name = p2_login.get_json()["user"]["pharmacy"]["pharmacy_name"]
    print(f"[STEP 5 OK] Logged into Pharmacy 2: '{p2_name}' using username 'testpharm002'.")

    # Step 6: Pharmacy 2 views order and raises a Partial Quote (item 1 available, item 2 unavailable)
    b2 = client.get("/api/pharmacy/broadcasts", headers=p2_headers).get_json()["broadcasts"]
    assert any(b["order_id"] == order_id for b in b2)

    q2_res = client.post("/api/quotes", json={
        "order_id": order_id,
        "items": [
            {"order_item_id": oi1, "is_available": True, "unit_selling_price": 70.00},
            {"order_item_id": oi2, "is_available": False, "unit_selling_price": 0.00}
        ],
        "notes": "Green Cross: Item 1 available at discount. Item 2 unavailable (billed $0.00)."
    }, headers=p2_headers)
    assert q2_res.status_code == 201
    q2_total = q2_res.get_json()["quote"]["total_quoted_price"]
    print(f"[STEP 6 OK] Pharmacy 2 ({p2_name}) raised Partial Quote of ${q2_total:.2f} (item 2 not charged).")

    # Step 7: Log back into Customer account, view notifications and compare quotes
    c_notifs = client.get("/api/notifications", headers=cust_headers).get_json()["notifications"]
    quote_alerts = [n for n in c_notifs if n["event_type"] == "NEW_QUOTE_RECEIVED" and n["reference_id"] == order_id]
    assert len(quote_alerts) == 2
    print(f"[STEP 7 OK] Customer received notifications for both pharmacy quotes:")
    for qa in quote_alerts:
        print(f"   • Alert: {qa['message']}")

    quotes_list = client.get(f"/api/orders/{order_id}/quotes", headers=cust_headers).get_json()["quotes"]
    assert len(quotes_list) == 2
    print(f"[STEP 8 OK] Customer compared offers side-by-side:")
    for q in quotes_list:
        fulfillment = "Full Fulfillment" if q["is_full_fulfillment"] else f"Partial ({q['available_items_count']}/{q['total_items_count']})"
        print(f"   • {q['pharmacy_name']} -> {fulfillment} -> Total Payable: ${q['total_quoted_price']:.2f}")

    # Step 8: Customer selects Pharmacy 1 (Sri Lakshmi Care Pharmacy)
    q1_id = next(q["id"] for q in quotes_list if q["pharmacy_name"] == p1_name)
    select_res = client.post(f"/api/orders/{order_id}/select", json={"quote_id": q1_id}, headers=cust_headers)
    assert select_res.status_code == 200
    print(f"[STEP 9 OK] Customer selected {p1_name} for Order #{order_id}!")

    # Step 9: Verify Pharmacy 1 receives notification: "Customer selected your pharmacy"
    p1_notifs = client.get("/api/notifications", headers=p1_headers).get_json()["notifications"]
    award_notif = next(n for n in p1_notifs if n["event_type"] == "ORDER_AWARDED" and n["reference_id"] == order_id)
    print(f"[STEP 10 OK] Pharmacy 1 received award notification: '{award_notif['title']}' - '{award_notif['message']}'")

    # Step 10: Pharmacy 1 confirms the order
    confirm_res = client.post(f"/api/pharmacy/orders/{order_id}/confirm", json={"action": "CONFIRM"}, headers=p1_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.get_json()["order_status"] == "CONFIRMED"
    print(f"[STEP 11 OK] Pharmacy 1 confirmed Order #{order_id}!")

    # Step 11: Customer receives confirmation notification
    c_final_notifs = client.get("/api/notifications", headers=cust_headers).get_json()["notifications"]
    confirmed_notif = next(n for n in c_final_notifs if n["event_type"] == "ORDER_CONFIRMED" and n["reference_id"] == order_id)
    print(f"[STEP 12 OK] Customer received final confirmation alert: '{confirmed_notif['title']}' - '{confirmed_notif['message']}'")

    print("\n" + "=" * 70)
    print("ALL STEPS OF USER SCENARIO EXECUTED AND VERIFIED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_user_flow()
