from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from app.db import get_db, transaction
from app.utils.auth_helpers import token_required, role_required

pharmacy_bp = Blueprint("pharmacy_mgmt", __name__, url_prefix="/api/pharmacy")

@pharmacy_bp.route("/orders", methods=["GET"])
@token_required
@role_required("PHARMACY")
def list_assigned_orders():
    """
    Lists orders awarded to this pharmacy with customer details,
    confirmation status, and fulfillment stage.
    """
    db = get_db()
    status_filter = request.args.get("status")

    query = """
        SELECT o.id as order_id, o.customer_id, o.zone, o.delivery_address, o.status as order_status,
               o.total_mrp, o.final_amount, o.mock_payment_status, o.created_at as order_created_at,
               oa.id as assignment_id, oa.quote_id, oa.confirmation_status, oa.selected_at, oa.confirmed_at,
               u.full_name as customer_name, u.phone as customer_phone,
               q.total_quoted_price, q.is_full_fulfillment, q.available_items_count, q.total_items_count
        FROM order_assignments oa
        JOIN orders o ON oa.order_id = o.id
        JOIN users u ON o.customer_id = u.id
        JOIN quotes q ON oa.quote_id = q.id
        WHERE oa.pharmacy_id = ?
    """
    params = [g.user_id]

    if status_filter:
        query += " AND o.status = ?"
        params.append(status_filter)

    query += " ORDER BY oa.selected_at DESC"

    rows = db.execute(query, params).fetchall()

    orders = []
    for r in rows:
        # Fetch items
        items_rows = db.execute(
            """
            SELECT qi.id as quote_item_id, qi.is_available, qi.unit_selling_price, qi.subtotal_price, qi.notes,
                   oi.quantity, oi.unit_mrp,
                   m.name as medicine_name
            FROM quote_items qi
            JOIN order_items oi ON qi.order_item_id = oi.id
            JOIN medicines m ON oi.medicine_id = m.id
            WHERE qi.quote_id = ?
            """,
            (r["quote_id"],)
        ).fetchall()

        items = [
            {
                "medicine_name": ir["medicine_name"],
                "quantity": ir["quantity"],
                "unit_mrp": float(ir["unit_mrp"]),
                "is_available": bool(ir["is_available"]),
                "unit_selling_price": float(ir["unit_selling_price"]),
                "subtotal_price": float(ir["subtotal_price"]),
                "notes": ir["notes"]
            }
            for ir in items_rows
        ]

        orders.append({
            "order_id": r["order_id"],
            "assignment_id": r["assignment_id"],
            "quote_id": r["quote_id"],
            "order_status": r["order_status"],
            "confirmation_status": r["confirmation_status"],
            "selected_at": str(r["selected_at"]),
            "confirmed_at": str(r["confirmed_at"]) if r["confirmed_at"] else None,
            "final_amount": float(r["final_amount"]),
            "mock_payment_status": r["mock_payment_status"],
            "customer": {
                "id": r["customer_id"],
                "name": r["customer_name"],
                "phone": r["customer_phone"],
                "delivery_address": r["delivery_address"],
                "zone": r["zone"]
            },
            "fulfillment": {
                "is_full": bool(r["is_full_fulfillment"]),
                "available_items_count": r["available_items_count"],
                "total_items_count": r["total_items_count"]
            },
            "items": items
        })

    # Total earnings made by this pharmacy through customer orders
    earnings_row = db.execute(
        """
        SELECT COALESCE(SUM(o.final_amount), 0.0) as total_earnings
        FROM order_assignments oa
        JOIN orders o ON oa.order_id = o.id
        WHERE oa.pharmacy_id = ? AND oa.confirmation_status = 'CONFIRMED'
        """,
        (g.user_id,)
    ).fetchone()
    total_earnings = float(earnings_row["total_earnings"]) if earnings_row else 0.0

    accepted_count = db.execute(
        "SELECT COUNT(*) FROM order_assignments WHERE pharmacy_id = ? AND confirmation_status = 'CONFIRMED'",
        (g.user_id,)
    ).fetchone()[0]

    # Fetch rejected or expired records for this pharmacy
    rejected_rows = db.execute(
        """
        SELECT o.id as order_id, o.zone, o.delivery_address, o.status as order_status,
               o.total_mrp, o.created_at,
               COALESCE(oa.confirmation_status, 'EXPIRED') as rejection_type,
               COALESCE(u.full_name, 'Customer') as customer_name,
               COALESCE(q.total_quoted_price, o.total_mrp) as amount
        FROM orders o
        LEFT JOIN order_assignments oa ON o.id = oa.order_id AND oa.pharmacy_id = ?
        LEFT JOIN quotes q ON o.id = q.order_id AND q.pharmacy_id = ?
        JOIN users u ON o.customer_id = u.id
        JOIN pharmacy_profiles p ON LOWER(o.zone) = LOWER(p.zone)
        WHERE p.user_id = ?
          AND (
            oa.confirmation_status = 'REJECTED'
            OR o.status = 'EXPIRED'
            OR q.status IN ('REJECTED', 'EXPIRED')
            OR (o.status = 'BROADCASTING' AND o.broadcast_expires_at <= CURRENT_TIMESTAMP)
          )
        ORDER BY o.id DESC
        LIMIT 30
        """,
        (g.user_id, g.user_id, g.user_id)
    ).fetchall()

    rejected_list = [
        {
            "order_id": rej["order_id"],
            "zone": rej["zone"],
            "delivery_address": rej["delivery_address"],
            "order_status": rej["order_status"],
            "rejection_type": rej["rejection_type"],
            "customer_name": rej["customer_name"],
            "amount": float(rej["amount"] or 0),
            "created_at": str(rej["created_at"])
        }
        for rej in rejected_rows
    ]

    return jsonify({
        "assigned_orders": orders,
        "rejected_or_expired_orders": rejected_list,
        "metrics": {
            "total_earnings": total_earnings,
            "accepted_orders_count": accepted_count,
            "rejected_orders_count": len(rejected_list)
        }
    }), 200


@pharmacy_bp.route("/orders/<int:order_id>/confirm", methods=["POST"])
@token_required
@role_required("PHARMACY")
def confirm_order(order_id: int):
    """
    Pharmacy confirms or rejects an awarded order.
    Transitions order to CONFIRMED or REJECTED and notifies customer.
    """
    data = request.get_json() or {}
    action = (data.get("action") or "").strip().upper()
    reason = (data.get("rejection_reason") or "").strip()

    if action not in ("CONFIRM", "REJECT"):
        return jsonify({"error": "Action must be CONFIRM or REJECT"}), 400

    db = get_db()
    assignment = db.execute(
        """
        SELECT oa.id, oa.order_id, oa.confirmation_status, o.customer_id, p.pharmacy_name
        FROM order_assignments oa
        JOIN orders o ON oa.order_id = o.id
        JOIN pharmacy_profiles p ON oa.pharmacy_id = p.user_id
        WHERE oa.order_id = ? AND oa.pharmacy_id = ?
        """,
        (order_id, g.user_id)
    ).fetchone()

    if not assignment:
        return jsonify({"error": "Order assignment not found for this pharmacy"}), 404

    if assignment["confirmation_status"] != "PENDING":
        return jsonify({
            "error": f"Order has already been {assignment['confirmation_status'].lower()}ed"
        }), 400

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with transaction(db):
        if action == "CONFIRM":
            db.execute(
                """
                UPDATE order_assignments
                SET confirmation_status = 'CONFIRMED', confirmed_at = ?
                WHERE id = ?
                """,
                (now_str, assignment["id"])
            )
            db.execute("UPDATE orders SET status = 'CONFIRMED' WHERE id = ?", (order_id,))

            # Customer Notification
            db.execute(
                """
                INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                VALUES (?, ?, ?, 'ORDER_CONFIRMED', ?)
                """,
                (
                    assignment["customer_id"],
                    "Order Confirmed by Pharmacy",
                    f"{assignment['pharmacy_name']} confirmed your Order #{order_id}. Preparation is starting now.",
                    order_id
                )
            )
            msg = "Order confirmed successfully"
            new_status = "CONFIRMED"
        else:
            # Action: REJECT
            db.execute(
                """
                UPDATE order_assignments
                SET confirmation_status = 'REJECTED', confirmed_at = ?
                WHERE id = ?
                """,
                (now_str, assignment["id"])
            )

            # Check if alternative submitted quotes exist from other pharmacies
            other_quotes = db.execute(
                "SELECT id, pharmacy_id FROM quotes WHERE order_id = ? AND pharmacy_id != ?",
                (order_id, g.user_id)
            ).fetchall()

            if other_quotes:
                # Re-open selection for customer to choose an alternative quote
                new_status = "PENDING_SELECTION"
                db.execute("UPDATE orders SET status = 'PENDING_SELECTION' WHERE id = ?", (order_id,))
                # Re-open other quotes from REJECTED back to SUBMITTED so customer can re-select
                db.execute(
                    "UPDATE quotes SET status = 'SUBMITTED' WHERE order_id = ? AND pharmacy_id != ?",
                    (order_id, g.user_id)
                )
                # Remove active assignment lock so customer can choose alternative winner
                db.execute("DELETE FROM order_assignments WHERE id = ?", (assignment["id"],))

                reject_msg = f"{assignment['pharmacy_name']} was unable to fulfill Order #{order_id}."
                if reason:
                    reject_msg += f" Reason: {reason}."
                reject_msg += f" Alternative quotes from other pharmacies are available for you to review and select."

                db.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                    VALUES (?, ?, ?, 'ORDER_REJECTED_ALTERNATIVE_AVAILABLE', ?)
                    """,
                    (assignment["customer_id"], "Pharmacy Rejected — Alternative Quotes Available", reject_msg, order_id)
                )
            else:
                new_status = "REJECTED"
                db.execute("UPDATE orders SET status = 'REJECTED' WHERE id = ?", (order_id,))
                reject_msg = f"{assignment['pharmacy_name']} was unable to fulfill Order #{order_id}."
                if reason:
                    reject_msg += f" Reason: {reason}."
                reject_msg += " No alternative quotes were received for this broadcast."

                db.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, event_type, reference_id)
                    VALUES (?, ?, ?, 'ORDER_REJECTED', ?)
                    """,
                    (assignment["customer_id"], "Order Rejected by Pharmacy", reject_msg, order_id)
                )

            msg = "Order rejected"

    return jsonify({
        "message": msg,
        "order_id": order_id,
        "confirmation_status": action,
        "order_status": new_status
    }), 200


@pharmacy_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@token_required
@role_required("PHARMACY")
def update_fulfillment_status(order_id: int):
    """
    Updates forward fulfillment stages:
    CONFIRMED -> PREPARING -> DISPATCHED -> DELIVERED
    """
    data = request.get_json() or {}
    new_status = (data.get("status") or "").strip().upper()

    VALID_STAGES = ["PREPARING", "DISPATCHED", "DELIVERED"]
    if new_status not in VALID_STAGES:
        return jsonify({"error": f"Invalid stage. Allowed: {', '.join(VALID_STAGES)}"}), 400

    db = get_db()
    order = db.execute(
        """
        SELECT o.id, o.status, o.customer_id, oa.confirmation_status, p.pharmacy_name
        FROM orders o
        JOIN order_assignments oa ON o.id = oa.order_id
        JOIN pharmacy_profiles p ON oa.pharmacy_id = p.user_id
        WHERE o.id = ? AND oa.pharmacy_id = ?
        """,
        (order_id, g.user_id)
    ).fetchone()

    if not order:
        return jsonify({"error": "Order not found or not assigned to your pharmacy"}), 404

    if order["confirmation_status"] != "CONFIRMED":
        return jsonify({"error": "Order must be confirmed before progressing fulfillment stages"}), 400

    current_status = order["status"]

    # Validate logical forward progression
    progression = {
        "CONFIRMED": ["PREPARING", "DISPATCHED"],
        "PREPARING": ["DISPATCHED"],
        "DISPATCHED": ["DELIVERED"],
        "DELIVERED": []
    }
    allowed = progression.get(current_status, [])
    if new_status not in allowed:
        return jsonify({
            "error": f"Cannot transition from '{current_status}' to '{new_status}'. Allowed next stages: {', '.join(allowed) if allowed else 'None (Terminal)'}"
        }), 400

    with transaction(db):
        db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))

        status_messages = {
            "PREPARING": "Your medicines are being packed and checked.",
            "DISPATCHED": "Your medicines are on the way with delivery partner.",
            "DELIVERED": "Your medicines have been safely delivered."
        }

        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'STATUS_UPDATE', ?)
            """,
            (
                order["customer_id"],
                f"Order #{order_id} is {new_status.title()}",
                f"{order['pharmacy_name']} updated your order: {status_messages[new_status]}",
                order_id
            )
        )

    return jsonify({
        "message": f"Order status updated to {new_status}",
        "order_id": order_id,
        "status": new_status
    }), 200


@pharmacy_bp.route("/metrics", methods=["GET"])
@token_required
@role_required("PHARMACY")
def pharmacy_metrics():
    """Summary KPI metrics for pharmacy dashboard."""
    db = get_db()
    
    # Broadcast count in zone
    profile = db.execute("SELECT zone FROM pharmacy_profiles WHERE user_id = ?", (g.user_id,)).fetchone()
    zone = profile["zone"] if profile else "ZONE_A"

    active_broadcasts = db.execute(
        "SELECT COUNT(*) as cnt FROM orders WHERE zone = ? AND status = 'BROADCASTING'",
        (zone,)
    ).fetchone()["cnt"]

    my_quotes_cnt = db.execute(
        "SELECT COUNT(*) as cnt FROM quotes WHERE pharmacy_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    won_orders_cnt = db.execute(
        "SELECT COUNT(*) as cnt FROM order_assignments WHERE pharmacy_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    delivered_cnt = db.execute(
        """
        SELECT COUNT(*) as cnt FROM orders o
        JOIN order_assignments oa ON o.id = oa.order_id
        WHERE oa.pharmacy_id = ? AND o.status = 'DELIVERED'
        """,
        (g.user_id,)
    ).fetchone()["cnt"]

    total_revenue = db.execute(
        """
        SELECT COALESCE(SUM(o.final_amount), 0) as rev FROM orders o
        JOIN order_assignments oa ON o.id = oa.order_id
        WHERE oa.pharmacy_id = ? AND o.status IN ('CONFIRMED', 'PREPARING', 'DISPATCHED', 'DELIVERED')
        """,
        (g.user_id,)
    ).fetchone()["rev"]

    return jsonify({
        "metrics": {
            "active_zone_broadcasts": active_broadcasts,
            "quotes_submitted": my_quotes_cnt,
            "orders_won": won_orders_cnt,
            "orders_delivered": delivered_cnt,
            "total_revenue": round(float(total_revenue), 2)
        }
    }), 200
