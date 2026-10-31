from flask import Blueprint, request, jsonify, g
from app.db import get_db, transaction
from app.utils.auth_helpers import token_required, role_required
from app.services.broadcast_service import compute_remaining_seconds
from app.services.pricing_service import calculate_quote_pricing

quote_bp = Blueprint("quotes", __name__)

@quote_bp.route("/api/pharmacy/broadcasts", methods=["GET"])
@token_required
@role_required("PHARMACY")
def list_zone_broadcasts():
    """
    Lists active order broadcasts for the calling pharmacy's zone
    within the strict 4-minute window.
    """
    db = get_db()
    
    # Get pharmacy profile zone
    profile = db.execute(
        "SELECT zone, is_active FROM pharmacy_profiles WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()

    if not profile or not profile["is_active"]:
        return jsonify({"error": "Pharmacy profile is inactive or not found"}), 403

    pharmacy_zone = profile["zone"]

    orders_rows = db.execute(
        """
        SELECT o.id, o.customer_id, o.zone, o.delivery_address, o.status,
               o.broadcast_started_at, o.broadcast_expires_at, o.total_mrp, o.created_at,
               o.order_type, o.prescription_url, o.prescription_notes, o.is_ocr_scanned,
               obp.distance_km,
               (SELECT COUNT(*) FROM quotes WHERE order_id = o.id AND pharmacy_id = ?) as quoted_by_me
        FROM orders o
        JOIN order_broadcast_pharmacies obp ON o.id = obp.order_id
        WHERE obp.pharmacy_id = ? AND o.status = 'BROADCASTING'
        ORDER BY o.id DESC
        """,
        (g.user_id, g.user_id)
    ).fetchall()

    active_broadcasts = []
    for o in orders_rows:
        remaining = compute_remaining_seconds(o["broadcast_expires_at"])
        if remaining <= 0:
            # Window expired; automatically advance status if needed
            continue

        # Fetch items requested
        items_rows = db.execute(
            """
            SELECT oi.id, oi.medicine_id, oi.quantity, oi.unit_mrp, oi.subtotal_mrp,
                   m.name as medicine_name, m.dosage_form, m.pack_size, m.requires_prescription
            FROM order_items oi
            JOIN medicines m ON oi.medicine_id = m.id
            WHERE oi.order_id = ?
            """,
            (o["id"],)
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

        active_broadcasts.append({
            "order_id": o["id"],
            "zone": o["zone"],
            "delivery_address": o["delivery_address"],
            "distance_km": round(float(o["distance_km"]), 1) if "distance_km" in o.keys() and o["distance_km"] is not None else None,
            "status": o["status"],
            "order_type": o["order_type"] or "CATALOGUE",
            "prescription_url": o["prescription_url"],
            "prescription_notes": o["prescription_notes"],
            "is_ocr_scanned": bool(o["is_ocr_scanned"]),
            "broadcast_started_at": str(o["broadcast_started_at"]),
            "broadcast_expires_at": str(o["broadcast_expires_at"]),
            "remaining_broadcast_seconds": remaining,
            "total_mrp": float(o["total_mrp"]),
            "already_quoted": bool(o["quoted_by_me"]),
            "items": items,
            "created_at": str(o["created_at"])
        })

    return jsonify({"broadcasts": active_broadcasts}), 200


@quote_bp.route("/api/quotes", methods=["POST"])
@token_required
@role_required("PHARMACY")
def submit_quote():
    """
    Submits a full or partial quote for an order.
    Enforces:
      1. Exact 4-minute broadcast window. Past window, returns HTTP 410.
      2. Zone eligibility.
      3. Never charge for unavailable medicines (subtotal strictly 0.00).
      4. Single quote per pharmacy per order.
    """
    data = request.get_json() or {}
    order_id = data.get("order_id")
    items_quote = data.get("items") or []
    notes = (data.get("notes") or "").strip() or None

    if not order_id or not items_quote:
        return jsonify({"error": "order_id and items are required"}), 400

    db = get_db()

    # 1. Check Pharmacy Profile
    pharmacy = db.execute(
        "SELECT p.pharmacy_name, p.zone, p.is_active FROM pharmacy_profiles p WHERE p.user_id = ?",
        (g.user_id,)
    ).fetchone()

    if not pharmacy or not pharmacy["is_active"]:
        return jsonify({"error": "Pharmacy profile not active"}), 403

    # 2. Check Order & Zone
    order = db.execute(
        "SELECT id, customer_id, zone, status, broadcast_expires_at FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order["zone"].strip().lower() != pharmacy["zone"].strip().lower():
        return jsonify({"error": f"Pharmacy zone '{pharmacy['zone']}' does not match order zone '{order['zone']}'"}), 403

    # 3. CRITICAL REQUIREMENT: Strictly enforce 4-minute broadcast window
    remaining_seconds = compute_remaining_seconds(order["broadcast_expires_at"])
    if order["status"] != "BROADCASTING" or remaining_seconds <= 0:
        return jsonify({
            "error": "The 4-minute broadcast window has closed. Quotes can no longer be accepted for this order."
        }), 410

    # 4. Check if already quoted
    existing_quote = db.execute(
        "SELECT id FROM quotes WHERE order_id = ? AND pharmacy_id = ?",
        (order_id, g.user_id)
    ).fetchone()

    if existing_quote:
        return jsonify({"error": "You have already submitted a quote for this order"}), 409

    # 5. Calculate item-level pricing with zero charge guarantee for unavailable items
    try:
        total_price, avail_cnt, total_cnt, is_full, validated_items = calculate_quote_pricing(
            db=db,
            order_id=order_id,
            item_quotes=items_quote
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    # 6. Persist quote and quote items atomically
    with transaction(db):
        cursor = db.execute(
            """
            INSERT INTO quotes (
                order_id, pharmacy_id, status, total_quoted_price,
                available_items_count, total_items_count, is_full_fulfillment, notes
            )
            VALUES (?, ?, 'SUBMITTED', ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                g.user_id,
                total_price,
                avail_cnt,
                total_cnt,
                1 if is_full else 0,
                notes
            )
        )
        quote_id = cursor.lastrowid

        for vi in validated_items:
            db.execute(
                """
                INSERT INTO quote_items (
                    quote_id, order_item_id, is_available, unit_selling_price, subtotal_price, notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    quote_id,
                    vi["order_item_id"],
                    vi["is_available"],
                    vi["unit_selling_price"],
                    vi["subtotal_price"],
                    vi["notes"]
                )
            )

        # 7. Notify Customer
        fulfillment_str = "Full" if is_full else f"Partial ({avail_cnt}/{total_cnt} items)"
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'NEW_QUOTE_RECEIVED', ?)
            """,
            (
                order["customer_id"],
                "New Pharmacy Quote Received",
                f"{pharmacy['pharmacy_name']} submitted a {fulfillment_str} quote of ₹{total_price:.2f} for Order #{order_id}.",
                order_id
            )
        )

    return jsonify({
        "message": "Quote submitted successfully",
        "quote": {
            "id": quote_id,
            "order_id": order_id,
            "pharmacy_name": pharmacy["pharmacy_name"],
            "total_quoted_price": total_price,
            "available_items_count": avail_cnt,
            "total_items_count": total_cnt,
            "is_full_fulfillment": is_full,
            "items": validated_items
        }
    }), 201


@quote_bp.route("/api/orders/<int:order_id>/quotes", methods=["GET"])
@token_required
def get_order_quotes(order_id: int):
    """
    Returns all submitted quotes for an order, enabling customers to compare
    full vs partial fulfillment, MRP vs selling prices, and savings.
    """
    db = get_db()
    order = db.execute("SELECT id, customer_id, status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if g.role == "CUSTOMER" and order["customer_id"] != g.user_id:
        return jsonify({"error": "Access denied"}), 403

    quotes_rows = db.execute(
        """
        SELECT q.id, q.order_id, q.pharmacy_id, q.status, q.total_quoted_price,
               q.available_items_count, q.total_items_count, q.is_full_fulfillment,
               q.notes, q.submitted_at,
               p.pharmacy_name, p.address as pharmacy_address, p.license_number, p.zone as pharmacy_zone
        FROM quotes q
        JOIN pharmacy_profiles p ON q.pharmacy_id = p.user_id
        WHERE q.order_id = ?
        ORDER BY q.is_full_fulfillment DESC, q.total_quoted_price ASC
        """,
        (order_id,)
    ).fetchall()

    quotes = []
    for qr in quotes_rows:
        # Fetch item details
        items_rows = db.execute(
            """
            SELECT qi.id, qi.order_item_id, qi.is_available, qi.unit_selling_price, qi.subtotal_price, qi.notes,
                   oi.quantity, oi.unit_mrp, oi.subtotal_mrp,
                   m.name as medicine_name
            FROM quote_items qi
            JOIN order_items oi ON qi.order_item_id = oi.id
            JOIN medicines m ON oi.medicine_id = m.id
            WHERE qi.quote_id = ?
            """,
            (qr["id"],)
        ).fetchall()

        items = []
        for ir in items_rows:
            unit_mrp = float(ir["unit_mrp"])
            unit_selling = float(ir["unit_selling_price"])
            sub_mrp = float(ir["subtotal_mrp"])
            sub_price = float(ir["subtotal_price"])
            is_avail = bool(ir["is_available"])
            item_disc_pct = round(((unit_mrp - unit_selling) / unit_mrp) * 100, 1) if unit_mrp > 0 and unit_selling < unit_mrp else 0.0
            item_savings = max(0.0, round(sub_mrp - sub_price, 2)) if is_avail else 0.0

            items.append({
                "id": ir["id"],
                "order_item_id": ir["order_item_id"],
                "medicine_name": ir["medicine_name"],
                "quantity": ir["quantity"],
                "unit_mrp": unit_mrp,
                "subtotal_mrp": sub_mrp,
                "is_available": is_avail,
                "unit_selling_price": unit_selling,
                "subtotal_price": sub_price,
                "discount_pct": item_disc_pct,
                "savings": item_savings,
                "notes": ir["notes"]
            })

        total_mrp = sum(it["subtotal_mrp"] for it in items if it["is_available"])
        total_quoted_price = float(qr["total_quoted_price"])
        total_savings = max(0.0, round(total_mrp - total_quoted_price, 2))
        savings_pct = round((total_savings / total_mrp) * 100, 1) if total_mrp > 0 else 0.0

        quotes.append({
            "id": qr["id"],
            "order_id": qr["order_id"],
            "pharmacy_id": qr["pharmacy_id"],
            "pharmacy_name": qr["pharmacy_name"],
            "pharmacy_address": qr["pharmacy_address"],
            "pharmacy_zone": qr["pharmacy_zone"] if ("pharmacy_zone" in qr.keys() and qr["pharmacy_zone"]) else "",
            "license_number": qr["license_number"],
            "status": qr["status"],
            "total_mrp": total_mrp,
            "total_quoted_price": total_quoted_price,
            "total_savings": total_savings,
            "savings_pct": savings_pct,
            "available_items_count": qr["available_items_count"],
            "total_items_count": qr["total_items_count"],
            "is_full_fulfillment": bool(qr["is_full_fulfillment"]),
            "notes": qr["notes"],
            "submitted_at": str(qr["submitted_at"]),
            "items": items
        })

    return jsonify({"quotes": quotes}), 200


@quote_bp.route("/api/pharmacy/my-quotes", methods=["GET"])
@token_required
@role_required("PHARMACY")
def list_my_quotes():
    db = get_db()
    rows = db.execute(
        """
        SELECT q.id, q.order_id, q.status as quote_status, q.total_quoted_price,
               q.available_items_count, q.total_items_count, q.is_full_fulfillment,
               q.submitted_at, o.status as order_status, o.zone, o.delivery_address
        FROM quotes q
        JOIN orders o ON q.order_id = o.id
        WHERE q.pharmacy_id = ?
        ORDER BY q.id DESC
        """,
        (g.user_id,)
    ).fetchall()

    quotes = [
        {
            "id": r["id"],
            "order_id": r["order_id"],
            "quote_status": r["quote_status"],
            "order_status": r["order_status"],
            "zone": r["zone"],
            "delivery_address": r["delivery_address"],
            "total_quoted_price": float(r["total_quoted_price"]),
            "available_items_count": r["available_items_count"],
            "total_items_count": r["total_items_count"],
            "is_full_fulfillment": bool(r["is_full_fulfillment"]),
            "submitted_at": str(r["submitted_at"])
        }
        for r in rows
    ]
    return jsonify({"my_quotes": quotes}), 200
