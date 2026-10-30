from flask import Blueprint, request, jsonify, g
from app.db import get_db
from app.utils.auth_helpers import token_required, role_required
from app.services.selection_service import select_winning_quote, process_mock_payment, deselect_winning_quote

selection_bp = Blueprint("selection", __name__)

@selection_bp.route("/api/orders/<int:order_id>/select", methods=["POST"])
@token_required
@role_required("CUSTOMER")
def select_quote(order_id: int):
    """
    Selects exactly one winning pharmacy quote with database transaction protection.
    Prevents race conditions, double-selection, and locks the order to the winner.
    """
    data = request.get_json(silent=True) or {}
    quote_id = data.get("quote_id")

    if not quote_id:
        return jsonify({"error": "quote_id is required"}), 400

    db = get_db()
    try:
        result = select_winning_quote(
            db=db,
            order_id=order_id,
            customer_id=g.user_id,
            quote_id=int(quote_id)
        )
        return jsonify({
            "message": "Pharmacy selected successfully",
            "assignment": result
        }), 200
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except RuntimeError as re:
        # Concurrency / Double selection conflict
        return jsonify({"error": str(re)}), 409
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Selection failed: {str(e)}"}), 500


@selection_bp.route("/api/orders/<int:order_id>/deselect", methods=["POST"])
@token_required
@role_required("CUSTOMER")
def deselect_quote_route(order_id: int):
    """
    Deselects the currently assigned pharmacy before payment is made,
    allowing the customer to switch to another pharmacy or reconsider.
    """
    db = get_db()
    try:
        result = deselect_winning_quote(
            db=db,
            order_id=order_id,
            customer_id=g.user_id
        )
        return jsonify({
            "message": "Pharmacy selection cancelled successfully",
            "result": result
        }), 200
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to deselect pharmacy: {str(e)}"}), 500


@selection_bp.route("/api/orders/<int:order_id>/mock-pay", methods=["POST"])
@token_required
@role_required("CUSTOMER")
def pay_mock(order_id: int):
    """
    Simulated mock payment endpoint.
    Explicitly labelled as simulated test payment.
    """
    data = request.get_json(silent=True) or {}
    payment_method = data.get("payment_method", "SIMULATED_MOCK_CARD")

    db = get_db()
    try:
        result = process_mock_payment(
            db=db,
            order_id=order_id,
            customer_id=g.user_id,
            payment_method=payment_method
        )
        return jsonify({
            "message": "Simulated mock payment recorded",
            "payment": result
        }), 200
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Payment simulation failed: {str(e)}"}), 500
