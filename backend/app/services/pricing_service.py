from typing import Dict, Any, List, Tuple

def calculate_quote_pricing(
    db,
    order_id: int,
    item_quotes: List[Dict[str, Any]]
) -> Tuple[float, int, int, bool, List[Dict[str, Any]]]:
    """
    Rigorously validates and calculates item-level quote pricing.
    Strict business rules:
      - Preserve catalogue MRP.
      - Never charge for unavailable medicines (subtotal_price is strictly 0.00).
      - Unit selling price must be positive for available medicines.
      - Calculate total quoted price, available count, total count, and full fulfillment flag.
    """
    # Fetch all order items
    order_items_rows = db.execute(
        """
        SELECT oi.id, oi.medicine_id, oi.quantity, oi.unit_mrp, m.name as medicine_name
        FROM order_items oi
        JOIN medicines m ON oi.medicine_id = m.id
        WHERE oi.order_id = ?
        """,
        (order_id,)
    ).fetchall()

    if not order_items_rows:
        raise ValueError(f"No order items found for order #{order_id}")

    order_items_map = {row["id"]: row for row in order_items_rows}
    total_items_count = len(order_items_rows)

    validated_quote_items = []
    total_quoted_price = 0.0
    available_items_count = 0

    quote_dict = {q.get("order_item_id"): q for q in item_quotes if "order_item_id" in q}

    for oi_id, oi in order_items_map.items():
        q_item = quote_dict.get(oi_id)
        if not q_item:
            # If not specified in quote, default to unavailable
            is_available = False
            unit_price = 0.0
            subtotal = 0.0
            notes = "Not quoted (Unavailable)"
        else:
            raw_avail = q_item.get("is_available")
            if isinstance(raw_avail, bool):
                is_available = raw_avail
            elif isinstance(raw_avail, (int, float)):
                is_available = bool(raw_avail)
            elif isinstance(raw_avail, str):
                is_available = raw_avail.strip().lower() in ("true", "1", "yes")
            else:
                is_available = False

            raw_notes = q_item.get("notes") or ""
            notes = str(raw_notes).strip() or None

            if is_available:
                try:
                    unit_price = float(q_item.get("unit_selling_price", oi["unit_mrp"]))
                    if unit_price <= 0:
                        raise ValueError
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid unit selling price for '{oi['medicine_name']}'. Must be greater than 0.")
                
                subtotal = round(unit_price * oi["quantity"], 2)
                available_items_count += 1
                total_quoted_price += subtotal
            else:
                # STRICT REQUIREMENT: Never charge for unavailable medicines
                unit_price = 0.0
                subtotal = 0.0

        validated_quote_items.append({
            "order_item_id": oi_id,
            "medicine_name": oi["medicine_name"],
            "quantity": oi["quantity"],
            "unit_mrp": float(oi["unit_mrp"]),
            "is_available": 1 if is_available else 0,
            "unit_selling_price": unit_price,
            "subtotal_price": subtotal,
            "notes": notes
        })

    if available_items_count == 0:
        raise ValueError("Quote must have at least one available medicine.")

    total_quoted_price = round(total_quoted_price, 2)
    is_full_fulfillment = (available_items_count == total_items_count)

    return total_quoted_price, available_items_count, total_items_count, is_full_fulfillment, validated_quote_items
