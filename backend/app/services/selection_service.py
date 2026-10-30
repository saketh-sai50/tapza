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
            SELECT id, customer_id, zone, status, total_mrp, final_amount, mock_payment_status
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        if not order:
            raise ValueError(f"Order #{order_id} not found")

        if order["customer_id"] != customer_id:
            raise PermissionError("Access denied: You do not own this order")

        # Check if already paid. Once paid, pharmacy selection is locked.
        is_paid = order["mock_payment_status"] in ("MOCK_PAID", "PAID", "COMPLETED")
        if is_paid:
            raise ValueError(
                f"Payment has already been completed for Order #{order_id}. Pharmacy selection is locked and cannot be changed."
            )

        # Allow selecting/switching pharmacy while order is in BROADCASTING, PENDING_SELECTION, or CONFIRMED_PENDING_PHARMACY
        if order["status"] not in ("BROADCASTING", "PENDING_SELECTION", "CONFIRMED_PENDING_PHARMACY"):
            raise ValueError(f"Cannot select quote for order in status '{order['status']}'")

        # 2. Verify selected quote exists and belongs to this order
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

        winning_pharmacy_id = quote["pharmacy_id"]
        final_payable_amount = float(quote["total_quoted_price"])

        # 3. Seamlessly remove any prior assignment for this order before assigning new winner
        db.execute("DELETE FROM order_assignments WHERE order_id = ?", (order_id,))

        # 4. Insert atomic assignment record
        cursor = db.execute(
            """
            INSERT INTO order_assignments (order_id, quote_id, pharmacy_id, confirmation_status)
            VALUES (?, ?, ?, 'PENDING')
            """,
            (order_id, quote_id, winning_pharmacy_id)
        )
        assignment_id = cursor.lastrowid

        # 5. Mark all quotes for this order as SUBMITTED, and winning quote as SELECTED
        db.execute("UPDATE quotes SET status = 'SUBMITTED' WHERE order_id = ?", (order_id,))
        db.execute("UPDATE quotes SET status = 'SELECTED' WHERE id = ?", (quote_id,))

        # 6. Update Order status and final amount
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


def deselect_winning_quote(
    db,
    order_id: int,
    customer_id: int
) -> Dict[str, Any]:
    """
    Deselects the currently assigned pharmacy before payment is made.
    Restores the order back to BROADCASTING status and resets all quotes to SUBMITTED,
    allowing the customer to choose any other pharmacy or reconsider.
    """
    with transaction(db):
        order = db.execute(
            """
            SELECT id, customer_id, zone, status, mock_payment_status
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        if not order:
            raise ValueError(f"Order #{order_id} not found")

        if order["customer_id"] != customer_id:
            raise PermissionError("Access denied: You do not own this order")

        # Cannot deselect if already paid!
        is_paid = order["mock_payment_status"] in ("MOCK_PAID", "PAID", "COMPLETED")
        if is_paid:
            raise ValueError(
                f"Payment has already been completed for Order #{order_id}. Pharmacy selection is locked and cannot be deselected."
            )

        # Remove assignment
        db.execute("DELETE FROM order_assignments WHERE order_id = ?", (order_id,))

        # Reset all quotes for this order back to SUBMITTED
        db.execute("UPDATE quotes SET status = 'SUBMITTED' WHERE order_id = ?", (order_id,))

        # Reset order status back to BROADCASTING and clear final_amount
        db.execute(
            """
            UPDATE orders
            SET status = 'BROADCASTING',
                final_amount = 0.0
            WHERE id = ?
            """,
            (order_id,)
        )

        # Notify customer
        db.execute(
            """
            INSERT INTO notifications (user_id, title, message, event_type, reference_id)
            VALUES (?, ?, ?, 'QUOTE_DESELECTED', ?)
            """,
            (
                customer_id,
                "Pharmacy Selection Cancelled",
                f"You deselected the pharmacy for Order #{order_id}. You can select any other quote or wait for new offers.",
                order_id
            )
        )

    return {
        "order_id": order_id,
        "status": "BROADCASTING",
        "deselected": True,
        "message": "Pharmacy deselected. You can now choose any pharmacy quote."
    }
