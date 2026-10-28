import json
from app import create_app

app = create_app()

def run_tests():
    print("=== Testing Stage 8: Admin Dashboards & Data Management ===")
    client = app.test_client()

    # 1. Admin Login
    res_a = client.post("/api/auth/login", json={"email": "admin@tapza.com", "password": "Admin@123"})
    assert res_a.status_code == 200
    admin_token = res_a.get_json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[OK] Admin authenticated.")

    # 2. Customer Login to test RBAC rejection
    res_c = client.post("/api/auth/login", json={"email": "customer.test@example.com", "password": "Password123!"})
    cust_token = res_c.get_json()["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 3. RBAC Security Check
    rbac_res = client.get("/api/admin/metrics", headers=cust_headers)
    assert rbac_res.status_code == 403, f"Customer should be denied from admin metrics: {rbac_res.status_code}"
    print("[OK] RBAC verified: Customer denied access to admin endpoints (403 Forbidden).")

    # 4. Admin Metrics API
    metrics_res = client.get("/api/admin/metrics", headers=admin_headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.get_json()["metrics"]
    assert metrics["users"]["total"] >= 3
    assert metrics["orders"]["total"] >= 1
    assert metrics["platform_gmv"] >= 0
    assert len(metrics["zones"]) >= 1
    print(f"[OK] Admin platform metrics verified: {metrics['orders']['total']} total orders, GMV ${metrics['platform_gmv']:.2f}, {metrics['users']['pharmacies']} pharmacies.")

    # 5. Admin Pharmacies List & Status Toggle
    pharm_res = client.get("/api/admin/pharmacies", headers=admin_headers)
    assert pharm_res.status_code == 200
    pharmacies = pharm_res.get_json()["pharmacies"]
    assert len(pharmacies) >= 2
    target_p = pharmacies[0]
    p_id = target_p["user_id"]
    orig_active = target_p["is_active"]
    print(f"[OK] Admin retrieved {len(pharmacies)} onboarded pharmacies. Testing target: '{target_p['pharmacy_name']}'.")

    # Toggle to suspend
    tog_res1 = client.post(f"/api/admin/pharmacies/{p_id}/toggle", headers=admin_headers)
    assert tog_res1.status_code == 200
    assert tog_res1.get_json()["is_active"] == (not orig_active)
    print(f"[OK] Pharmacy status successfully toggled (is_active={tog_res1.get_json()['is_active']}).")

    # Toggle back to restore original state
    tog_res2 = client.post(f"/api/admin/pharmacies/{p_id}/toggle", headers=admin_headers)
    assert tog_res2.status_code == 200
    assert tog_res2.get_json()["is_active"] == orig_active
    print("[OK] Pharmacy status restored to active.")

    # 6. Admin Update Pharmacy Operating Zone
    zone_res = client.put(f"/api/admin/pharmacies/{p_id}/zone", json={"zone": "ZONE_B"}, headers=admin_headers)
    assert zone_res.status_code == 200
    assert zone_res.get_json()["zone"] == "ZONE_B"
    print("[OK] Admin successfully updated pharmacy operating zone to 'ZONE_B'.")

    # Restore zone to ZONE_A
    client.put(f"/api/admin/pharmacies/{p_id}/zone", json={"zone": "ZONE_A"}, headers=admin_headers)

    # 7. Admin Global Orders Audit Log
    orders_res = client.get("/api/admin/orders", headers=admin_headers)
    assert orders_res.status_code == 200
    audit_orders = orders_res.get_json()["orders"]
    assert len(audit_orders) >= 1
    print(f"[OK] Global orders audit log verified: {len(audit_orders)} platform orders retrieved.")

    # Filtered audit log
    deliv_res = client.get("/api/admin/orders?status=DELIVERED", headers=admin_headers)
    assert deliv_res.status_code == 200
    deliv_orders = deliv_res.get_json()["orders"]
    for d in deliv_orders:
        assert d["status"] == "DELIVERED"
    print(f"[OK] Filtered audit log verified: {len(deliv_orders)} delivered orders retrieved.")

    # 8. User Management Endpoint
    users_res = client.get("/api/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    users_list = users_res.get_json()["users"]
    assert len(users_list) >= 3
    print(f"[OK] Admin user directory verified: {len(users_list)} registered user accounts.")

    print("\nALL STAGE 8 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
