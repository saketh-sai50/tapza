from typing import Dict, Any
from app.db import transaction

def select_winning_quote(
    db,
    order_id: int,
    customer_id: int,
    quote_id: int
) -> Dict[str, Any]:
    """
    Atomically selects a single pharmacy quote for an order.
    Guarantees concurrency safety using SQLite transaction locking (BEGIN IMMEDIATE).
    Strict requirements:
      - Only the order customer can select.
      - Exactly one pharmacy can be assigned (prevents double-selection / race conditions).
      - Updates winning quote to SELECTED and all other quotes to REJECTED.
      - Sets order final_amount to winning quote's total (guaranteeing zero charge for unavailable items).
      - Persists notifications for both parties.
    """
    with transaction(db):
        # 1. Fetch order and lock row
        order = db.execute(
            """
            SELECT id, customer_id, zone, status, total_mrp, final_amount
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        if not order:
            raise ValueError(f"Order #{order_id} not found")

        if order["customer_id"] != customer_id:
            raise PermissionError("Access denied: You do not own this order")

        # 2. Concurrency Check: Verify no existing assignment
        existing_assignment = db.execute(
            "SELECT id, pharmacy_id, quote_id FROM order_assignments WHERE order_id = ?",
            (order_id,)
        ).fetchone()

        if existing_assignment:
            raise RuntimeError(
                f"Conflict: Order #{order_id} has already been assigned to Pharmacy #{existing_assignment['pharmacy_id']}."
            )

        if order["status"] not in ("BROADCASTING", "PENDING_SELECTION"):
            raise ValueError(f"Cannot select quote for order in status '{order['status']}'")

        # 3. Verify selected quote exists and belongs to this order
        quote = db.execute(
            """
            SELECT q.id, q.order_id, q.pharmacy_id, q.status, q.total_quoted_price,
                   q.available_items_count, q.total_items_count, q.is_full_fulfillment,
                   p.pharmacy_name
            FROM quotes q
            JOIN pharmacy_profiles p ON q.pharmacy_id = p.user_id
            WHERE q.id = ? AND q.order_id = ?
            """,
            (quote_id, order_id)
        ).fetchone()

        if not quote:
            raise ValueError(f"Quote #{quote_id} not found for Order #{order_id}")

        if quote["status"] != "SUBMITTED":
            raise ValueError(f"Quote #{quote_id} is in status '{quote['status']}' and cannot be selected")

        winning_pharmacy_id = quote["pharmacy_id"]
        final_payable_amount = float(quote["total_quoted_price"])

        # 4. Insert atomic assignment record (Strict 1-to-1 unique constraint)
        cursor = db.execute(
            """
            INSERT INTO order_assignments (order_id, quote_id, pharmacy_id, confirmation_status)
            VALUES (?, ?, ?, 'PENDING')
            """,
            (order_id, quote_id, winning_pharmacy_id)
        )
        assignment_id = cursor.lastrowid

        # 5. Mark winning quote SELECTED
        db.execute("UPDATE quotes SET status = 'SELECTED' WHERE id = ?", (quote_id,))

        # 6. Mark all other competing quotes REJECTED
        db.execute(
            "UPDATE quotes SET status = 'REJECTED' WHERE order_id = ? AND id != ?",
            (order_id, quote_id)
        )

        # 7. Update Order status and final amount
        db.execute(
            """
            UPDATE orders
            SET status = 'CONFIRMED_PENDING_PHARMACY',
                final_amount = ?
            WHERE id = ?
            """,
            (final_payable_amount, order_id)
        )

        # 8. Send Notification to Winning Pharmacy
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'ORDER_AWARDED', ?)
            """,
            (
                winning_pharmacy_id,
                "Order Awarded! Pending Your Confirmation",
                f"Customer selected your quote for Order #{order_id} (₹{final_payable_amount:.2f}). Please review and confirm dispatch.",
                order_id
            )
        )

        # 9. Send Notification to Customer
        fulfillment_type = "Full" if quote["is_full_fulfillment"] else f"Partial ({quote['available_items_count']}/{quote['total_items_count']} items)"
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'QUOTE_SELECTED', ?)
            """,
            (
                customer_id,
                "Pharmacy Selected",
                f"You selected {quote['pharmacy_name']} ({fulfillment_type}) for Order #{order_id}. Total payable: ₹{final_payable_amount:.2f}.",
                order_id
            )
        )

    return {
        "assignment_id": assignment_id,
        "order_id": order_id,
        "selected_quote_id": quote_id,
        "pharmacy_id": winning_pharmacy_id,
        "pharmacy_name": quote["pharmacy_name"],
        "final_payable_amount": final_payable_amount,
        "is_full_fulfillment": bool(quote["is_full_fulfillment"]),
        "order_status": "CONFIRMED_PENDING_PHARMACY"
    }


def process_mock_payment(
    db,
    order_id: int,
    customer_id: int,
    payment_method: str = "SIMULATED_MOCK_CARD"
) -> Dict[str, Any]:
    """
    Simulates test payment clearly labelled as a mock transaction.
    """
    with transaction(db):
        order = db.execute(
            """
            SELECT o.id, o.customer_id, o.status, o.final_amount, o.mock_payment_status,
                   oa.pharmacy_id
            FROM orders o
            LEFT JOIN order_assignments oa ON o.id = oa.order_id
            WHERE o.id = ?
            """,
            (order_id,)
        ).fetchone()

        if not order:
            raise ValueError(f"Order #{order_id} not found")

        if order["customer_id"] != customer_id:
            raise PermissionError("Access denied")

        if not order["pharmacy_id"]:
            raise ValueError("Cannot pay for an order before selecting a pharmacy quote")

        # Update payment status
        db.execute(
            "UPDATE orders SET mock_payment_status = 'MOCK_PAID' WHERE id = ?",
            (order_id,)
        )

        amount = float(order["final_amount"])
        cust_row = db.execute("SELECT full_name, phone FROM users WHERE id = ?", (customer_id,)).fetchone()
        cust_name = cust_row["full_name"] if cust_row else "Customer"
        pharmacy_id = order["pharmacy_id"]

        # 1. Persist notification for the Customer
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'MOCK_PAYMENT_COMPLETED', ?)
            """,
            (
                customer_id,
                "Simulated Test Payment Successful",
                f"[MOCK] Simulated test payment of ₹{amount:.2f} processed via {payment_method}. No real charges made.",
                order_id
            )
        )

        # 2. Persist notification for the Winning Pharmacy
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'PAYMENT_RECEIVED', ?)
            """,
            (
                pharmacy_id,
                "💰 Payment Received! Money Transferred Successfully",
                f"Customer {cust_name} has made the payment of ₹{amount:.2f} for Order #{order_id}. Money transferred successfully to your account! Please prepare and dispatch the order.",
                order_id
            )
        )

    return {
        "order_id": order_id,
        "mock_payment_status": "MOCK_PAID",
        "amount_paid": float(order["final_amount"]),
        "is_mock": True,
        "disclaimer": "Simulated mock payment for demonstration. No financial transaction occurred."
    }
