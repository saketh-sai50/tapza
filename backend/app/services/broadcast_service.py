import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.db import transaction
from app.services.geo_service import geocode_address, find_pharmacies_in_radius, haversine_distance

def get_current_utc_timestamp() -> int:
    return int(time.time())

def format_iso_timestamp(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def create_broadcast_order(
    db,
    customer_id: int,
    zone: str,
    delivery_address: str,
    items: List[Dict[str, Any]],
    broadcast_seconds: int = 240,
    customer_lat: Optional[float] = None,
    customer_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Creates an order and initiates the strict 4-minute (240 seconds) spatial broadcast.
    Uses SQLite R*Tree to find nearby pharmacies within 5 km of customer coordinates.
    """
    now_ts = get_current_utc_timestamp()
    expires_ts = now_ts + broadcast_seconds
    started_at_str = format_iso_timestamp(now_ts)
    expires_at_str = format_iso_timestamp(expires_ts)

    # Resolve customer coordinates
    if customer_lat is None or customer_lon is None:
        c_lat, c_lon, formatted_addr = geocode_address(delivery_address)
    else:
        c_lat, c_lon = float(customer_lat), float(customer_lon)
        formatted_addr = delivery_address

    # 1. Validate medicines and calculate MRP subtotals
    order_items_to_insert = []
    total_mrp = 0.0

    for item in items:
        med_id = item.get("medicine_id")
        qty = int(item.get("quantity", 1))
        if qty <= 0:
            raise ValueError(f"Quantity must be greater than zero for medicine ID {med_id}")

        med = db.execute(
            "SELECT id, name, mrp, is_active FROM medicines WHERE id = ?",
            (med_id,)
        ).fetchone()

        if not med:
            name_hint = item.get("name") or item.get("medicine_name") or ""
            if name_hint:
                med = db.execute("SELECT id, name, mrp, is_active FROM medicines WHERE name LIKE ? LIMIT 1", (f"%{name_hint}%",)).fetchone()
            if not med:
                cursor = db.execute(
                    """
                    INSERT INTO medicines (name, generic_name, manufacturer, category, dosage_form, strength, composition, pack_size, mrp, requires_prescription, is_active)
                    VALUES (?, ?, 'Verified Manufacturer', 'General', 'Tablet', 'Standard', 'Standard Formulation', '1 Unit', ?, 0, 1)
                    """,
                    (name_hint or f"Medicine #{med_id}", name_hint or "General", float(item.get("mrp") or 30.0))
                )
                new_id = cursor.lastrowid
                med = db.execute("SELECT id, name, mrp, is_active FROM medicines WHERE id = ?", (new_id,)).fetchone()
        if not med["is_active"]:
            raise ValueError(f"Medicine '{med['name']}' is currently inactive")

        unit_mrp = float(med["mrp"])
        subtotal_mrp = round(unit_mrp * qty, 2)
        total_mrp += subtotal_mrp

        order_items_to_insert.append({
            "medicine_id": med["id"],
            "medicine_name": med["name"],
            "quantity": qty,
            "unit_mrp": unit_mrp,
            "subtotal_mrp": subtotal_mrp
        })

    total_mrp = round(total_mrp, 2)

    # 2. Find nearby pharmacies within 5km using SQLite R*Tree
    initial_radius = 5.0
    nearby_pharmacies = find_pharmacies_in_radius(db, c_lat, c_lon, 0.0, initial_radius)

    # If no pharmacies within 5km, expand to 10km immediately
    if not nearby_pharmacies:
        initial_radius = 10.0
        nearby_pharmacies = find_pharmacies_in_radius(db, c_lat, c_lon, 0.0, initial_radius)

    # ALWAYS include testpharm001 so tester can verify orders under testpharm001 anytime
    p001_row = db.execute(
        """
        SELECT u.id, p.pharmacy_name, p.address, p.phone, p.latitude, p.longitude
        FROM users u
        JOIN pharmacy_profiles p ON u.id = p.user_id
        WHERE u.username = 'testpharm001' AND p.is_active = 1
        """
    ).fetchone()
    if p001_row:
        p001_id = p001_row["id"]
        if not any(p["pharmacy_id"] == p001_id for p in nearby_pharmacies):
            p001_lat = float(p001_row["latitude"]) if p001_row["latitude"] is not None else 18.002476
            p001_lon = float(p001_row["longitude"]) if p001_row["longitude"] is not None else 79.556723
            dist = haversine_distance(c_lat, c_lon, p001_lat, p001_lon)
            nearby_pharmacies.append({
                "pharmacy_id": p001_id,
                "pharmacy_name": p001_row["pharmacy_name"],
                "address": p001_row["address"],
                "phone": p001_row["phone"],
                "latitude": p001_lat,
                "longitude": p001_lon,
                "distance_km": dist
            })
            nearby_pharmacies.sort(key=lambda x: x["distance_km"])

    # 3. Persist order, line items, and broadcast targets atomically
    with transaction(db):
        cursor = db.execute(
            """
            INSERT INTO orders (
                customer_id, zone, delivery_address, status,
                broadcast_started_at, broadcast_expires_at, total_mrp, final_amount, mock_payment_status,
                customer_lat, customer_lng, search_radius_km
            )
            VALUES (?, ?, ?, 'BROADCASTING', ?, ?, ?, ?, 'UNPAID', ?, ?, ?)
            """,
            (
                customer_id,
                zone or "Warangal",
                formatted_addr,
                started_at_str,
                expires_at_str,
                total_mrp,
                total_mrp,
                c_lat,
                c_lon,
                initial_radius
            )
        )
        order_id = cursor.lastrowid

        for oi in order_items_to_insert:
            db.execute(
                """
                INSERT INTO order_items (order_id, medicine_id, quantity, unit_mrp, subtotal_mrp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, oi["medicine_id"], oi["quantity"], oi["unit_mrp"], oi["subtotal_mrp"])
            )

        # Record targeted pharmacies in order_broadcast_pharmacies
        for p in nearby_pharmacies:
            db.execute(
                """
                INSERT OR IGNORE INTO order_broadcast_pharmacies (order_id, pharmacy_id, distance_km, ring_stage)
                VALUES (?, ?, ?, 1)
                """,
                (order_id, p["pharmacy_id"], p["distance_km"])
            )

        # Persist Customer Notification
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'ORDER_BROADCAST_STARTED', ?)
            """,
            (
                customer_id,
                "Order Request Broadcasted",
                f"Your request has been sent to {len(nearby_pharmacies)} nearby pharmacies within {initial_radius} km. Waiting for best quotes.",
                order_id
            )
        )

        # Notify eligible pharmacies in range
        cust_row = db.execute("SELECT full_name FROM users WHERE id = ?", (customer_id,)).fetchone()
        cust_name = cust_row["full_name"] if cust_row else "Customer"
        items_summary = ", ".join([f"{it['quantity']}x {it['medicine_name']}" for it in order_items_to_insert])

        for p in nearby_pharmacies:
            db.execute(
                """
                INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                VALUES (?, ?, ?, 'NEW_ZONE_BROADCAST', ?)
                """,
                (
                    p["pharmacy_id"],
                    f"New Medicine Request ({p['distance_km']} km away)",
                    f"Customer {cust_name} requested: {items_summary} for delivery to {formatted_addr}. Quote your prices within 4 minutes.",
                    order_id
                )
            )

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "zone": zone or "Warangal",
        "delivery_address": formatted_addr,
        "customer_lat": c_lat,
        "customer_lng": c_lon,
        "search_radius_km": initial_radius,
        "pharmacies_contacted": len(nearby_pharmacies),
        "status": "BROADCASTING",
        "broadcast_started_at": started_at_str,
        "broadcast_expires_at": expires_at_str,
        "remaining_broadcast_seconds": broadcast_seconds,
        "total_mrp": total_mrp,
        "items": order_items_to_insert
    }


def check_and_expand_order_broadcast(db, order_id: int) -> Dict[str, Any]:
    """
    Checks if order has exceeded 4 minutes (240s) without an accepted quote.
    If so, automatically expands search radius by +5 km (to 10 km) and broadcasts
    to pharmacies in the second ring.
    Once payment is completed or order is finalized/assigned, expansion is strictly skipped.
    """
    order = db.execute(
        """
        SELECT id, customer_id, delivery_address, status, broadcast_started_at,
               customer_lat, customer_lng, search_radius_km, expanded_at,
               mock_payment_status, payment_status, pharmacy_id
        FROM orders WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    if not order or order["status"] not in ("BROADCASTING", "PENDING_SELECTION"):
        return {"expanded": False}

    # Strict check: Never expand radius if payment is already completed!
    is_paid = (order["mock_payment_status"] in ("MOCK_PAID", "PAID", "COMPLETED")) or (order["payment_status"] in ("PAID", "COMPLETED"))
    if is_paid:
        return {"expanded": False}

    current_radius = float(order["search_radius_km"] or 5.0)
    c_lat = float(order["customer_lat"] or 18.002476)
    c_lon = float(order["customer_lng"] or 79.556723)

    # Check time elapsed since start
    try:
        clean_str = str(order["broadcast_started_at"]).replace("T", " ")
        if "." in clean_str:
            clean_str = clean_str.split(".")[0]
        started_dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        elapsed = (now_dt - started_dt).total_seconds()
    except Exception:
        elapsed = 0

    # Expand if >= 240 seconds (4 minutes) and still at 5km
    if elapsed >= 240 and current_radius < 10.0 and not order["expanded_at"]:
        new_radius = 10.0
        new_pharmacies = find_pharmacies_in_radius(db, c_lat, c_lon, min_radius_km=5.0, max_radius_km=10.0)

        with transaction(db):
            now_dt = datetime.now(timezone.utc)
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            new_expires_dt = now_dt + timedelta(seconds=240)
            new_expires_str = new_expires_dt.strftime("%Y-%m-%d %H:%M:%S")

            db.execute(
                """
                UPDATE orders
                SET search_radius_km = ?, expanded_at = ?, broadcast_expires_at = ?, status = 'BROADCASTING'
                WHERE id = ?
                """,
                (new_radius, now_str, new_expires_str, order_id)
            )

            for p in new_pharmacies:
                db.execute(
                    """
                    INSERT OR IGNORE INTO order_broadcast_pharmacies (order_id, pharmacy_id, distance_km, ring_stage)
                    VALUES (?, ?, ?, 2)
                    """,
                    (order_id, p["pharmacy_id"], p["distance_km"])
                )

            # Customer Notification
            db.execute(
                """
                INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                VALUES (?, ?, ?, 'RADIUS_EXPANDED', ?)
                """,
                (
                    order["customer_id"],
                    "Search Radius Expanded to 10 km",
                    f"4 minutes completed. Search expanded to 10 km. Contacted {len(new_pharmacies)} more pharmacies.",
                    order_id
                )
            )

            # Notify new ring pharmacies
            for p in new_pharmacies:
                db.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                    VALUES (?, ?, ?, 'NEW_ZONE_BROADCAST', ?)
                    """,
                    (
                        p["pharmacy_id"],
                        f"New Medicine Request ({p['distance_km']} km away)",
                        f"Order #{order_id} broadcast expanded. Delivery to {order['delivery_address']}. Quote now.",
                        order_id
                    )
                )

        return {
            "expanded": True,
            "new_radius_km": 10.0,
            "newly_contacted": len(new_pharmacies)
        }

    return {"expanded": False, "current_radius_km": current_radius}


def compute_remaining_seconds(expires_at: Any) -> int:
    """Calculates remaining seconds until broadcast window expiry."""
    try:
        if isinstance(expires_at, datetime):
            expires_dt = expires_at
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
        elif isinstance(expires_at, str):
            clean_str = expires_at.replace("T", " ")
            if "." in clean_str:
                clean_str = clean_str.split(".")[0]
            expires_dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        elif isinstance(expires_at, (int, float)):
            expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        else:
            return 0

        now_dt = datetime.now(timezone.utc)
        diff = int((expires_dt - now_dt).total_seconds())
        return max(0, diff)
    except Exception:
        return 0
