from flask import Blueprint, request, jsonify, g, current_app
from app.db import get_db, transaction
from app.utils.auth_helpers import token_required, role_required
from app.services.broadcast_service import (
    create_broadcast_order,
    compute_remaining_seconds,
    get_current_utc_timestamp,
    format_iso_timestamp
)

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

def generate_auto_quotes_for_order(db, order_id: int, zone: str, customer_id: int):
    """
    Simulates real-time competitive pharmacy quotes for the order from nearby contacted pharmacies.
    CRITICAL ISOLATION: Manual testing accounts (testpharm001, testpharm002, testpharm003) are strictly
    EXCLUDED from auto-quotes so they remain 100% clean, unquoted, and independently actionable by testers.
    """
    try:
        pharmacies = db.execute(
            """
            SELECT u.id, u.full_name, p.pharmacy_name, obp.distance_km
            FROM order_broadcast_pharmacies obp
            JOIN users u ON obp.pharmacy_id = u.id
            JOIN pharmacy_profiles p ON u.id = p.user_id
            WHERE obp.order_id = ?
              AND p.is_active = 1
              AND (u.username IS NULL OR (u.username NOT IN ('testpharm001', 'testpharm002', 'testpharm003')))
              AND (u.email IS NULL OR (u.email NOT IN ('pharma.central@example.com', 'greenvalley@example.com')))
            ORDER BY obp.distance_km ASC
            LIMIT 2
            """,
            (order_id,)
        ).fetchall()

        if len(pharmacies) < 1:
            pharmacies = db.execute(
                """
                SELECT u.id, u.full_name, p.pharmacy_name, 2.0 as distance_km
                FROM users u
                JOIN pharmacy_profiles p ON u.id = p.user_id
                WHERE p.is_active = 1
                  AND (u.username IS NULL OR (u.username NOT IN ('testpharm001', 'testpharm002', 'testpharm003')))
                  AND (u.email IS NULL OR (u.email NOT IN ('pharma.central@example.com', 'greenvalley@example.com')))
                LIMIT 2
                """
            ).fetchall()

        if not pharmacies:
            return

        order_items = db.execute(
            "SELECT id, medicine_id, quantity, unit_mrp, subtotal_mrp FROM order_items WHERE order_id = ?",
            (order_id,)
        ).fetchall()

        if not order_items:
            return

        discounts = [0.15, 0.22, 0.10]
        med_notes_list = [
            "Original sealed strip from licensed batch. Expiry: 2027.",
            "Genuine manufacturer packaging with verifiable hologram. Take after food.",
            "Full course available in fresh inventory. 100% authentic medicine."
        ]
        notes_list = [
            "Genuine sealed batch in stock. Free fast doorstep delivery.",
            "Best price guaranteed. Verified licensed pharmacist packaging.",
            "Fresh inventory with complimentary doctor teleconsultation card."
        ]

        with transaction(db):
            for idx, p in enumerate(pharmacies):
                p_id = p["id"]
                p_name = p["pharmacy_name"] or p["full_name"]
                disc = discounts[idx % len(discounts)]
                p_notes = notes_list[idx % len(notes_list)]
                med_note = med_notes_list[idx % len(med_notes_list)]

                total_quoted = 0.0
                quote_item_rows = []

                for oi in order_items:
                    unit_mrp = float(oi["unit_mrp"])
                    qty = int(oi["quantity"])
                    selling_price = round(unit_mrp * (1.0 - disc), 2)
                    subtotal = round(selling_price * qty, 2)
                    total_quoted += subtotal
                    quote_item_rows.append((oi["id"], 1, selling_price, subtotal, med_note))

                total_quoted = round(total_quoted, 2)

                existing = db.execute(
                    "SELECT id FROM quotes WHERE order_id = ? AND pharmacy_id = ?",
                    (order_id, p_id)
                ).fetchone()
                if existing:
                    continue

                q_cur = db.execute(
                    """
                    INSERT INTO quotes (order_id, pharmacy_id, status, total_quoted_price, available_items_count, total_items_count, is_full_fulfillment, notes)
                    VALUES (?, ?, 'SUBMITTED', ?, ?, ?, 1, ?)
                    """,
                    (order_id, p_id, total_quoted, len(order_items), len(order_items), p_notes)
                )
                quote_id = q_cur.lastrowid

                for qi in quote_item_rows:
                    db.execute(
                        """
                        INSERT INTO quote_items (quote_id, order_item_id, is_available, unit_selling_price, subtotal_price, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (quote_id, qi[0], qi[1], qi[2], qi[3], qi[4])
                    )

                db.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                    VALUES (?, ?, ?, 'NEW_QUOTE_RECEIVED', ?)
                    """,
                    (
                        customer_id,
                        f"Quote from {p_name}",
                        f"{p_name} offered a competitive quote of ₹{total_quoted:.2f} ({int(disc*100)}% OFF).",
                        order_id
                    )
                )
    except Exception as e:
        print(f"Auto-quote simulation error: {e}")


@order_bp.route("", methods=["POST"])
@token_required
@role_required("CUSTOMER")
def create_order():
    data = request.get_json() or {}
    items = data.get("items") or []
    delivery_address = (data.get("delivery_address") or "").strip()
    zone = (data.get("zone") or g.zone or "Warangal").strip()
    customer_lat = data.get("customer_lat") or data.get("latitude")
    customer_lon = data.get("customer_lng") or data.get("customer_lon") or data.get("longitude")

    if not items or not isinstance(items, list):
        return jsonify({"error": "Order must contain at least one medicine item"}), 400

    if not delivery_address:
        return jsonify({"error": "Delivery address is required"}), 400

    db = get_db()
    broadcast_seconds = current_app.config.get("BROADCAST_WINDOW_SECONDS", 240)

    try:
        result = create_broadcast_order(
            db=db,
            customer_id=g.user_id,
            zone=zone,
            delivery_address=delivery_address,
            items=items,
            broadcast_seconds=broadcast_seconds,
            customer_lat=customer_lat,
            customer_lon=customer_lon
        )
        # Generate competitive pharmacy bids so customer experiences reverse-auction bidding instantly
        generate_auto_quotes_for_order(db=db, order_id=result["order_id"], zone=zone, customer_id=g.user_id)
        return jsonify({
            "message": "Order created and broadcasted successfully",
            "order": result
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create order: {str(e)}"}), 500


@order_bp.route("/prescription", methods=["POST"])
@token_required
@role_required("CUSTOMER")
def create_prescription_order():
    data = request.get_json() or {}
    prescription_image = (data.get("prescription_image") or "").strip()
    delivery_address = (data.get("delivery_address") or "").strip()
    zone = (data.get("zone") or g.zone or "Warangal").strip()
    notes = (data.get("notes") or "").strip()
    customer_lat = data.get("customer_lat") or data.get("latitude")
    customer_lon = data.get("customer_lng") or data.get("customer_lon") or data.get("longitude")

    if not prescription_image:
        return jsonify({"error": "Prescription image is required"}), 400

    if not delivery_address:
        return jsonify({"error": "Delivery address is required"}), 400

    db = get_db()
    broadcast_seconds = current_app.config.get("BROADCAST_WINDOW_SECONDS", 240)
    now_ts = get_current_utc_timestamp()
    expires_ts = now_ts + broadcast_seconds
    started_at_str = format_iso_timestamp(now_ts)
    expires_at_str = format_iso_timestamp(expires_ts)

    from app.services.geo_service import geocode_address, find_pharmacies_in_radius
    if customer_lat is None or customer_lon is None:
        c_lat, c_lon, formatted_addr = geocode_address(delivery_address)
    else:
        c_lat, c_lon = float(customer_lat), float(customer_lon)
        formatted_addr = delivery_address

    nearby_pharmacies = find_pharmacies_in_radius(db, c_lat, c_lon, 0.0, 5.0)
    if not nearby_pharmacies:
        nearby_pharmacies = find_pharmacies_in_radius(db, c_lat, c_lon, 0.0, 10.0)

    try:
        with transaction(db):
            cursor = db.execute(
                """
                INSERT INTO orders (
                    customer_id, zone, delivery_address, status,
                    broadcast_started_at, broadcast_expires_at, total_mrp, final_amount, mock_payment_status,
                    order_type, prescription_url, prescription_notes, is_ocr_scanned,
                    customer_lat, customer_lng, search_radius_km
                )
                VALUES (?, ?, ?, 'BROADCASTING', ?, ?, 0.0, 0.0, 'UNPAID', 'PRESCRIPTION', ?, ?, 0, ?, ?, 5.0)
                """,
                (
                    g.user_id,
                    zone,
                    formatted_addr,
                    started_at_str,
                    expires_at_str,
                    prescription_image,
                    notes,
                    c_lat,
                    c_lon
                )
            )
            order_id = cursor.lastrowid

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
                VALUES (?, ?, ?, 'ORDER_REQUEST_PLACED', ?)
                """,
                (
                    g.user_id,
                    "Prescription Broadcasted",
                    f"Your prescription has been sent to {len(nearby_pharmacies)} nearby pharmacies within 5 km. Waiting for bids.",
                    order_id
                )
            )

            cust_row = db.execute("SELECT full_name FROM users WHERE id = ?", (g.user_id,)).fetchone()
            cust_name = cust_row["full_name"] if cust_row else "Customer"

            for p in nearby_pharmacies:
                db.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                    VALUES (?, ?, ?, 'NEW_PRESCRIPTION_BROADCAST', ?)
                    """,
                    (
                        p["pharmacy_id"],
                        f"New Prescription Request ({p['distance_km']} km away)",
                        f"Customer {cust_name} uploaded a doctor prescription for delivery to {formatted_addr}. Open your dashboard and quote prices.",
                        order_id
                    )
                )

        return jsonify({
            "message": "Prescription order created and broadcasted successfully",
            "order": {
                "order_id": order_id,
                "customer_id": g.user_id,
                "zone": zone,
                "delivery_address": delivery_address,
                "status": "BROADCASTING",
                "order_type": "PRESCRIPTION",
                "prescription_url": prescription_image,
                "prescription_notes": notes,
                "remaining_broadcast_seconds": broadcast_seconds
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create prescription order: {str(e)}"}), 500


@order_bp.route("/<int:order_id>/scan-prescription", methods=["POST"])
@token_required
def scan_order_prescription(order_id: int):
    """
    Pharmacy or customer triggers OCR scan on prescription.
    Extracts prescribed medicines and matches them against catalog.
    """
    data = request.get_json() or {}
    client_ocr_text = data.get("ocr_text")

    db = get_db()
    from app.services.ocr_service import process_prescription_ocr
    try:
        res = process_prescription_ocr(db=db, order_id=order_id, client_ocr_text=client_ocr_text)
        return jsonify(res), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {str(e)}"}), 500


@order_bp.route("/<int:order_id>/items/add", methods=["POST"])
@token_required
def add_order_item(order_id: int):
    """Adds a new medicine item to an active order. Pharmacist can freely type medicine name from physical shop without searching catalog."""
    data = request.get_json() or {}
    medicine_id = data.get("medicine_id")
    medicine_name = (data.get("medicine_name") or data.get("name") or "").strip()
    quantity = int(data.get("quantity", 10))
    custom_price = data.get("price") or data.get("unit_mrp")

    if quantity <= 0:
        return jsonify({"error": "Quantity must be greater than 0"}), 400

    if not medicine_id and not medicine_name:
        return jsonify({"error": "Medicine name or ID is required"}), 400

    db = get_db()
    if medicine_id:
        med = db.execute("SELECT id, name, mrp, dosage_form, pack_size FROM medicines WHERE id = ?", (medicine_id,)).fetchone()
        if not med:
            return jsonify({"error": f"Medicine #{medicine_id} not found"}), 404
        name = med["name"]
        med_id = med["id"]
        dosage_form = med["dosage_form"] or "Tablet"
        pack_size = med["pack_size"] or "Unit"
        unit_mrp = float(custom_price) if custom_price is not None and float(custom_price) > 0 else float(med["mrp"])
    else:
        # Pharmacist freely typed medicine name from physical shelf!
        name = medicine_name
        unit_mrp = float(custom_price) if custom_price is not None and float(custom_price) > 0 else 50.0
        existing = db.execute("SELECT id, dosage_form, pack_size FROM medicines WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        if existing:
            med_id = existing["id"]
            dosage_form = existing["dosage_form"] or "Tablet"
            pack_size = existing["pack_size"] or "Unit"
        else:
            with transaction(db):
                cur_m = db.execute(
                    """
                    INSERT INTO medicines (name, generic_name, dosage_form, mrp, pack_size, is_active)
                    VALUES (?, ?, 'Tablet', ?, 'Unit', 1)
                    """,
                    (name, name, unit_mrp)
                )
                med_id = cur_m.lastrowid
            dosage_form = "Tablet"
            pack_size = "Unit"

    subtotal_mrp = round(unit_mrp * quantity, 2)

    with transaction(db):
        cur = db.execute(
            """
            INSERT INTO order_items (order_id, medicine_id, quantity, unit_mrp, subtotal_mrp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, med_id, quantity, unit_mrp, subtotal_mrp)
        )
        item_id = cur.lastrowid

        tot = db.execute("SELECT SUM(subtotal_mrp) as total FROM order_items WHERE order_id = ?", (order_id,)).fetchone()["total"] or 0.0
        db.execute("UPDATE orders SET total_mrp = ?, final_amount = ? WHERE id = ?", (tot, tot, order_id))

    return jsonify({
        "message": "Medicine added successfully",
        "item": {
            "id": item_id,
            "medicine_id": med_id,
            "medicine_name": name,
            "quantity": quantity,
            "unit_mrp": unit_mrp,
            "subtotal_mrp": subtotal_mrp,
            "dosage_form": dosage_form,
            "pack_size": pack_size
        },
        "order_total_mrp": round(tot, 2)
    }), 201


@order_bp.route("/<int:order_id>/items/<int:item_id>/replace", methods=["PUT", "POST"])
@token_required
def replace_order_item(order_id: int, item_id: int):
    """Pharmacist directly edits/replaces a medicine name without needing online catalog search."""
    data = request.get_json() or {}
    new_medicine_id = data.get("medicine_id")
    medicine_name = (data.get("medicine_name") or data.get("name") or "").strip()
    quantity = data.get("quantity")
    custom_price = data.get("price") or data.get("unit_mrp")

    if not new_medicine_id and not medicine_name:
        return jsonify({"error": "Medicine name or ID is required"}), 400

    db = get_db()
    existing_item = db.execute("SELECT id, medicine_id, quantity, unit_mrp FROM order_items WHERE id = ? AND order_id = ?", (item_id, order_id)).fetchone()
    if not existing_item:
        return jsonify({"error": "Order item not found"}), 404

    qty = int(quantity) if quantity is not None and int(quantity) > 0 else existing_item["quantity"]

    if new_medicine_id:
        med = db.execute("SELECT id, name, mrp, dosage_form, pack_size FROM medicines WHERE id = ?", (new_medicine_id,)).fetchone()
        if not med:
            return jsonify({"error": "Replacement medicine not found"}), 404
        med_id = med["id"]
        name = med["name"]
        dosage_form = med["dosage_form"] or "Tablet"
        pack_size = med["pack_size"] or "Unit"
        unit_mrp = float(custom_price) if custom_price is not None and float(custom_price) > 0 else float(med["mrp"])
    else:
        # Pharmacist directly typed a new/corrected medicine name!
        name = medicine_name
        unit_mrp = float(custom_price) if custom_price is not None and float(custom_price) > 0 else float(existing_item["unit_mrp"])
        existing = db.execute("SELECT id, dosage_form, pack_size FROM medicines WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        if existing:
            med_id = existing["id"]
            dosage_form = existing["dosage_form"] or "Tablet"
            pack_size = existing["pack_size"] or "Unit"
        else:
            with transaction(db):
                cur_m = db.execute(
                    """
                    INSERT INTO medicines (name, generic_name, dosage_form, mrp, pack_size, is_active)
                    VALUES (?, ?, 'Tablet', ?, 'Unit', 1)
                    """,
                    (name, name, unit_mrp)
                )
                med_id = cur_m.lastrowid
            dosage_form = "Tablet"
            pack_size = "Unit"

    subtotal_mrp = round(unit_mrp * qty, 2)

    with transaction(db):
        db.execute(
            """
            UPDATE order_items
            SET medicine_id = ?, quantity = ?, unit_mrp = ?, subtotal_mrp = ?
            WHERE id = ?
            """,
            (med_id, qty, unit_mrp, subtotal_mrp, item_id)
        )

        tot = db.execute("SELECT SUM(subtotal_mrp) as total FROM order_items WHERE order_id = ?", (order_id,)).fetchone()["total"] or 0.0
        db.execute("UPDATE orders SET total_mrp = ?, final_amount = ? WHERE id = ?", (tot, tot, order_id))

    return jsonify({
        "message": "Medicine updated successfully",
        "item": {
            "id": item_id,
            "medicine_id": med_id,
            "medicine_name": name,
            "quantity": qty,
            "unit_mrp": unit_mrp,
            "subtotal_mrp": subtotal_mrp,
            "dosage_form": dosage_form,
            "pack_size": pack_size
        },
        "order_total_mrp": round(tot, 2)
    }), 200


@order_bp.route("/<int:order_id>/items/<int:item_id>", methods=["DELETE"])
@token_required
def delete_order_item(order_id: int, item_id: int):
    """Pharmacist deletes an unwanted or wrongly recognized medicine from quote."""
    db = get_db()
    existing_item = db.execute("SELECT id FROM order_items WHERE id = ? AND order_id = ?", (item_id, order_id)).fetchone()
    if not existing_item:
        return jsonify({"error": "Order item not found"}), 404

    with transaction(db):
        db.execute("DELETE FROM order_items WHERE id = ?", (item_id,))
        tot = db.execute("SELECT COALESCE(SUM(subtotal_mrp), 0.0) as total FROM order_items WHERE order_id = ?", (order_id,)).fetchone()["total"]
        db.execute("UPDATE orders SET total_mrp = ?, final_amount = ? WHERE id = ?", (tot, tot, order_id))

    cnt = db.execute("SELECT COUNT(*) as cnt FROM order_items WHERE order_id = ?", (order_id,)).fetchone()["cnt"]
    return jsonify({
        "message": "Item deleted successfully",
        "remaining_count": cnt,
        "order_total_mrp": round(tot, 2)
    }), 200


@order_bp.route("/<int:order_id>/items/<int:item_id>/quantity", methods=["PUT", "POST"])
@token_required
def update_item_quantity(order_id: int, item_id: int):
    """Updates prescribed/quoted quantity for an item."""
    data = request.get_json() or {}
    quantity = int(data.get("quantity", 1))
    if quantity <= 0:
        return jsonify({"error": "Quantity must be greater than 0"}), 400

    db = get_db()
    item = db.execute("SELECT id, unit_mrp FROM order_items WHERE id = ? AND order_id = ?", (item_id, order_id)).fetchone()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    subtotal_mrp = round(float(item["unit_mrp"]) * quantity, 2)
    with transaction(db):
        db.execute("UPDATE order_items SET quantity = ?, subtotal_mrp = ? WHERE id = ?", (quantity, subtotal_mrp, item_id))
        tot = db.execute("SELECT SUM(subtotal_mrp) as total FROM order_items WHERE order_id = ?", (order_id,)).fetchone()["total"] or 0.0
        db.execute("UPDATE orders SET total_mrp = ?, final_amount = ? WHERE id = ?", (tot, tot, order_id))

    return jsonify({
        "message": "Quantity updated",
        "item_id": item_id,
        "quantity": quantity,
        "subtotal_mrp": subtotal_mrp,
        "order_total_mrp": round(tot, 2)
    }), 200


@order_bp.route("/my-orders", methods=["GET"])
@token_required
@role_required("CUSTOMER")
def list_my_orders():
    db = get_db()
    rows = db.execute(
        """
        SELECT o.id, o.zone, o.delivery_address, o.status,
               o.broadcast_started_at, o.broadcast_expires_at,
               o.total_mrp, o.final_amount, o.mock_payment_status, o.created_at,
               o.order_type, o.prescription_url, o.prescription_notes, o.is_ocr_scanned,
               (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count,
               (SELECT COUNT(*) FROM quotes WHERE order_id = o.id) as quote_count,
               oa.pharmacy_id as assigned_pharmacy_id,
               oa.confirmation_status as pharmacy_confirmation_status,
               p.pharmacy_name as assigned_pharmacy_name
        FROM orders o
        LEFT JOIN order_assignments oa ON o.id = oa.order_id
        LEFT JOIN pharmacy_profiles p ON oa.pharmacy_id = p.user_id
        WHERE o.customer_id = ?
        ORDER BY o.id DESC
        """,
        (g.user_id,)
    ).fetchall()

    orders = []
    for r in rows:
        remaining = compute_remaining_seconds(r["broadcast_expires_at"]) if r["status"] == "BROADCASTING" else 0
        items_rows = db.execute(
            """
            SELECT oi.medicine_id, oi.quantity, m.name as medicine_name, m.mrp, m.strength
            FROM order_items oi
            JOIN medicines m ON oi.medicine_id = m.id
            WHERE oi.order_id = ?
            """,
            (r["id"],)
        ).fetchall()
        order_items = [
            {
                "medicine_id": it["medicine_id"],
                "name": it["medicine_name"],
                "quantity": it["quantity"],
                "mrp": float(it["mrp"]),
                "strength": it["strength"]
            }
            for it in items_rows
        ]

        orders.append({
            "id": r["id"],
            "zone": r["zone"],
            "delivery_address": r["delivery_address"],
            "status": r["status"],
            "order_type": r["order_type"] or "CATALOGUE",
            "prescription_url": r["prescription_url"],
            "prescription_notes": r["prescription_notes"],
            "is_ocr_scanned": bool(r["is_ocr_scanned"]),
            "broadcast_started_at": str(r["broadcast_started_at"]),
            "broadcast_expires_at": str(r["broadcast_expires_at"]),
            "remaining_broadcast_seconds": remaining,
            "total_mrp": float(r["total_mrp"]),
            "final_amount": float(r["final_amount"]) if r["final_amount"] is not None else float(r["total_mrp"]),
            "mock_payment_status": r["mock_payment_status"],
            "item_count": r["item_count"],
            "quote_count": r["quote_count"],
            "items": order_items,
            "assigned_pharmacy": {
                "id": r["assigned_pharmacy_id"],
                "name": r["assigned_pharmacy_name"],
                "confirmation_status": r["pharmacy_confirmation_status"]
            } if r["assigned_pharmacy_id"] else None,
            "created_at": str(r["created_at"])
        })

    return jsonify({"orders": orders}), 200


@order_bp.route("/<int:order_id>", methods=["GET"])
@token_required
def get_order_details(order_id: int):
    db = get_db()
    order = db.execute(
        """
        SELECT o.id, o.customer_id, o.zone, o.delivery_address, o.status,
               o.broadcast_started_at, o.broadcast_expires_at,
               o.total_mrp, o.final_amount, o.mock_payment_status, o.created_at,
               o.order_type, o.prescription_url, o.prescription_notes, o.is_ocr_scanned,
               u.full_name as customer_name, u.phone as customer_phone,
               oa.pharmacy_id as assigned_pharmacy_id,
               oa.quote_id as assigned_quote_id,
               oa.confirmation_status as pharmacy_confirmation_status,
               p.pharmacy_name as assigned_pharmacy_name
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        LEFT JOIN order_assignments oa ON o.id = oa.order_id
        LEFT JOIN pharmacy_profiles p ON oa.pharmacy_id = p.user_id
        WHERE o.id = ?
        """,
        (order_id,)
    ).fetchone()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    # RBAC Access Check: Customer can view their own, Admin can view all, Pharmacy can view if zone matches or assigned
    if g.role == "CUSTOMER" and order["customer_id"] != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    # Items with preserved MRP
    items_rows = db.execute(
        """
        SELECT oi.id, oi.medicine_id, oi.quantity, oi.unit_mrp, oi.subtotal_mrp,
               m.name as medicine_name, m.dosage_form, m.pack_size, m.requires_prescription
        FROM order_items oi
        JOIN medicines m ON oi.medicine_id = m.id
        WHERE oi.order_id = ?
        """,
        (order_id,)
    ).fetchall()

    items = [
        {
            "id": ir["id"],
            "medicine_id": ir["medicine_id"],
            "medicine_name": ir["medicine_name"],
            "dosage_form": ir["dosage_form"],
            "pack_size": ir["pack_size"],
            "requires_prescription": bool(ir["requires_prescription"]),
            "quantity": ir["quantity"],
            "unit_mrp": float(ir["unit_mrp"]),
            "subtotal_mrp": float(ir["subtotal_mrp"])
        }
        for ir in items_rows
    ]

    remaining = compute_remaining_seconds(order["broadcast_expires_at"]) if order["status"] == "BROADCASTING" else 0

    # Auto transition or expand radius if broadcast timer elapsed and still marked BROADCASTING
    current_status = order["status"]
    if current_status in ("BROADCASTING", "PENDING_SELECTION") and remaining == 0:
        from app.services.broadcast_service import check_and_expand_order_broadcast
        exp_res = check_and_expand_order_broadcast(db, order_id)
        if exp_res.get("expanded"):
            # Radius expanded to 10 km! Refresh order and keep BROADCASTING with new timer
            refreshed = db.execute("SELECT status, broadcast_expires_at FROM orders WHERE id = ?", (order_id,)).fetchone()
            current_status = refreshed["status"]
            remaining = compute_remaining_seconds(refreshed["broadcast_expires_at"])
        else:
            quotes_count = db.execute("SELECT COUNT(*) as cnt FROM quotes WHERE order_id = ?", (order_id,)).fetchone()["cnt"]
            new_status = "PENDING_SELECTION" if quotes_count > 0 else "EXPIRED"
            with transaction(db):
                db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            current_status = new_status

    return jsonify({
        "order": {
            "id": order["id"],
            "customer_id": order["customer_id"],
            "customer_name": order["customer_name"],
            "customer_phone": order["customer_phone"],
            "zone": order["zone"],
            "delivery_address": order["delivery_address"],
            "status": current_status,
            "order_type": order["order_type"] or "CATALOGUE",
            "prescription_url": order["prescription_url"],
            "prescription_notes": order["prescription_notes"],
            "is_ocr_scanned": bool(order["is_ocr_scanned"]),
            "broadcast_started_at": str(order["broadcast_started_at"]),
            "broadcast_expires_at": str(order["broadcast_expires_at"]),
            "remaining_broadcast_seconds": remaining,
            "total_mrp": float(order["total_mrp"]),
            "final_amount": float(order["final_amount"]) if order["final_amount"] is not None else float(order["total_mrp"]),
            "mock_payment_status": order["mock_payment_status"],
            "assigned_pharmacy": {
                "id": order["assigned_pharmacy_id"],
                "name": order["assigned_pharmacy_name"],
                "quote_id": order["assigned_quote_id"],
                "confirmation_status": order["pharmacy_confirmation_status"]
            } if order["assigned_pharmacy_id"] else None,
            "items": items,
            "created_at": str(order["created_at"])
        }
    }), 200


@order_bp.route("/<int:order_id>/cancel", methods=["POST"])
@token_required
@role_required("CUSTOMER")
def cancel_order(order_id: int):
    db = get_db()
    order = db.execute(
        "SELECT id, customer_id, status FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order["customer_id"] != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    if order["status"] not in ("BROADCASTING", "PENDING_SELECTION"):
        return jsonify({"error": f"Cannot cancel order in status '{order['status']}'"}), 400

    with transaction(db):
        db.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = ?", (order_id,))
        db.execute("UPDATE quotes SET status = 'EXPIRED' WHERE order_id = ?", (order_id,))
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'ORDER_CANCELLED', ?)
            """,
            (g.user_id, "Order Cancelled", f"Your order #{order_id} has been cancelled.", order_id)
        )

    return jsonify({"message": "Order cancelled successfully"}), 200


@order_bp.route("/<int:order_id>/radar", methods=["GET"])
@token_required
def get_order_radar(order_id: int):
    """
    Returns live spatial radar metrics and dynamic Geoapify map URL for the order.
    Checks and expands broadcast radius to 10 km if 4 minutes have passed without quote selection.
    """
    db = get_db()
    from app.services.broadcast_service import check_and_expand_order_broadcast, compute_remaining_seconds
    from app.services.geo_service import generate_radar_static_map_url

    # Check 4-minute auto-expansion
    check_and_expand_order_broadcast(db, order_id)

    order = db.execute(
        """
        SELECT id, customer_id, zone, delivery_address, status,
               customer_lat, customer_lng, search_radius_km,
               broadcast_started_at, broadcast_expires_at, expanded_at
        FROM orders WHERE id = ?
        """,
        (order_id,)
    ).fetchone()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    c_lat = float(order["customer_lat"] or 18.002476)
    c_lon = float(order["customer_lng"] or 79.556723)
    radius_km = float(order["search_radius_km"] or 5.0)

    # Fetch targeted pharmacies for this order
    contacted_rows = db.execute(
        """
        SELECT obp.pharmacy_id, obp.distance_km, obp.ring_stage,
               p.pharmacy_name, p.address, p.phone, p.latitude, p.longitude,
               (SELECT status FROM quotes WHERE order_id = obp.order_id AND pharmacy_id = obp.pharmacy_id) as quote_status,
               (SELECT total_quoted_price FROM quotes WHERE order_id = obp.order_id AND pharmacy_id = obp.pharmacy_id) as quoted_price
        FROM order_broadcast_pharmacies obp
        JOIN pharmacy_profiles p ON obp.pharmacy_id = p.user_id
        WHERE obp.order_id = ?
        ORDER BY obp.distance_km ASC
        """,
        (order_id,)
    ).fetchall()

    # Fallback if order was created before R*Tree migration
    if not contacted_rows:
        from app.services.geo_service import find_pharmacies_in_radius
        found = find_pharmacies_in_radius(db, c_lat, c_lon, 0.0, radius_km)
        for p in found:
            db.execute(
                """
                INSERT OR IGNORE INTO order_broadcast_pharmacies (order_id, pharmacy_id, distance_km, ring_stage)
                VALUES (?, ?, ?, 1)
                """,
                (order_id, p["pharmacy_id"], p["distance_km"])
            )
        db.commit()
        contacted_rows = db.execute(
            """
            SELECT obp.pharmacy_id, obp.distance_km, obp.ring_stage,
                   p.pharmacy_name, p.address, p.phone, p.latitude, p.longitude,
                   (SELECT status FROM quotes WHERE order_id = obp.order_id AND pharmacy_id = obp.pharmacy_id) as quote_status,
                   (SELECT total_quoted_price FROM quotes WHERE order_id = obp.order_id AND pharmacy_id = obp.pharmacy_id) as quoted_price
            FROM order_broadcast_pharmacies obp
            JOIN pharmacy_profiles p ON obp.pharmacy_id = p.user_id
            WHERE obp.order_id = ?
            ORDER BY obp.distance_km ASC
            """,
            (order_id,)
        ).fetchall()

    # Winning / accepted pharmacy
    accepted = db.execute(
        """
        SELECT oa.pharmacy_id, p.pharmacy_name, p.address, p.phone, p.latitude, p.longitude,
               oa.confirmation_status, q.total_quoted_price
        FROM order_assignments oa
        JOIN pharmacy_profiles p ON oa.pharmacy_id = p.user_id
        JOIN quotes q ON oa.quote_id = q.id
        WHERE oa.order_id = ?
        """,
        (order_id,)
    ).fetchone()

    # Explicitly selected quote (customer clicked Accept / Select Quote)
    selected_quote = db.execute(
        """
        SELECT q.pharmacy_id, p.pharmacy_name, q.total_quoted_price, q.status,
               p.address, p.phone, p.latitude, p.longitude
        FROM quotes q
        JOIN pharmacy_profiles p ON q.pharmacy_id = p.user_id
        WHERE q.order_id = ? AND q.status = 'SELECTED'
        ORDER BY q.total_quoted_price ASC
        LIMIT 1
        """,
        (order_id,)
    ).fetchone()

    accepted_id = accepted["pharmacy_id"] if accepted else (selected_quote["pharmacy_id"] if selected_quote else None)
    accepted_info = None
    if accepted:
        accepted_info = {
            "pharmacy_id": accepted["pharmacy_id"],
            "pharmacy_name": accepted["pharmacy_name"],
            "address": accepted["address"],
            "phone": accepted["phone"],
            "confirmation_status": accepted["confirmation_status"],
            "total_price": float(accepted["total_quoted_price"])
        }
    elif selected_quote:
        accepted_info = {
            "pharmacy_id": selected_quote["pharmacy_id"],
            "pharmacy_name": selected_quote["pharmacy_name"],
            "address": selected_quote["address"],
            "phone": selected_quote["phone"],
            "confirmation_status": "CONFIRMED",
            "total_price": float(selected_quote["total_quoted_price"])
        }

    contacted_list = [
        {
            "pharmacy_id": cr["pharmacy_id"],
            "pharmacy_name": cr["pharmacy_name"],
            "address": cr["address"],
            "phone": cr["phone"],
            "latitude": float(cr["latitude"]) if cr["latitude"] else None,
            "longitude": float(cr["longitude"]) if cr["longitude"] else None,
            "distance_km": float(cr["distance_km"]),
            "ring_stage": cr["ring_stage"],
            "quote_status": cr["quote_status"],
            "quoted_price": float(cr["quoted_price"]) if cr["quoted_price"] else None
        }
        for cr in contacted_rows
    ]

    map_url = generate_radar_static_map_url(
        customer_lat=c_lat,
        customer_lon=c_lon,
        contacted_pharmacies=contacted_list,
        accepted_pharmacy_id=accepted_id,
        current_radius_km=radius_km
    )

    remaining = compute_remaining_seconds(order["broadcast_expires_at"])

    return jsonify({
        "order_id": order_id,
        "status": order["status"],
        "customer": {
            "lat": c_lat,
            "lng": c_lon,
            "delivery_address": order["delivery_address"]
        },
        "search_radius_km": radius_km,
        "is_expanded": radius_km > 5.0,
        "remaining_seconds": remaining,
        "pharmacies_contacted_count": len(contacted_list),
        "contacted_pharmacies": contacted_list,
        "accepted_pharmacy": accepted_info,
        "map_url": map_url
    }), 200


@order_bp.route("/<int:order_id>/expand_radius", methods=["POST"])
@token_required
def force_expand_order_radius(order_id: int):
    """
    Manually forces or simulates the 4-minute +5km (to 10km) radius expansion.
    Finds and broadcasts to all pharmacies in Ring 2 (5km to 10km) and resets the timer for 240s.
    """
    db = get_db()
    from datetime import datetime, timezone, timedelta
    from app.services.geo_service import find_pharmacies_in_radius

    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    c_lat = float(order["customer_lat"] or 18.002476)
    c_lon = float(order["customer_lng"] or 79.556723)
    new_radius = 10.0
    new_pharmacies = find_pharmacies_in_radius(db, c_lat, c_lon, min_radius_km=5.0, max_radius_km=10.0)

    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    new_expires_dt = now_dt + timedelta(seconds=240)
    new_expires_str = new_expires_dt.strftime("%Y-%m-%d %H:%M:%S")

    with transaction(db):
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
                INSERT OR IGNORE INTO order_broadcast_pharmacies
                (order_id, pharmacy_id, distance_km, ring_stage)
                VALUES (?, ?, ?, 2)
                """,
                (order_id, p["pharmacy_id"], p["distance_km"])
            )

    return jsonify({
        "message": "Order broadcast successfully expanded to 10.0 km (+5.0 km)",
        "search_radius_km": 10.0,
        "additional_pharmacies_count": len(new_pharmacies)
    }), 200


# Notification blueprint endpoints
notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@notification_bp.route("", methods=["GET"])
@token_required
def list_notifications():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, title, message, event_type, reference_id, is_read, created_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 50
        """,
        (g.user_id,)
    ).fetchall()

    notifications = [
        {
            "id": r["id"],
            "title": r["title"],
            "message": r["message"],
            "event_type": r["event_type"],
            "reference_id": r["reference_id"],
            "is_read": bool(r["is_read"]),
            "created_at": r["created_at"]
        }
        for r in rows
    ]
    return jsonify({"notifications": notifications}), 200


@notification_bp.route("/<int:notif_id>/read", methods=["POST"])
@token_required
def mark_read(notif_id: int):
    db = get_db()
    with transaction(db):
        db.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
            (notif_id, g.user_id)
        )
    return jsonify({"message": "Notification marked as read"}), 200


@notification_bp.route("/read-all", methods=["POST"])
@token_required
def mark_all_read():
    db = get_db()
    with transaction(db):
        db.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (g.user_id,)
        )
    return jsonify({"message": "All notifications marked as read"}), 200
