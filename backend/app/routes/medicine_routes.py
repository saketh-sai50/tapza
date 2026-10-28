from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
from app.db import get_db, transaction
from app.utils.auth_helpers import token_required, role_required
from app.services.import_service import parse_and_validate_excel, generate_catalogue_template

medicine_bp = Blueprint("medicines", __name__, url_prefix="/api/medicines")

@medicine_bp.route("", methods=["GET"])
def list_medicines():
    """
    Search and list medicines with pagination.
    Available to Customers, Pharmacies, and Admins.
    """
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = max(1, min(100, int(request.args.get("limit", 20))))
    offset = (page - 1) * limit

    db = get_db()
    query_conditions = ["is_active = 1"]
    params = []

    if search:
        search_param = f"%{search}%"
        query_conditions.append(
            "(name LIKE ? OR generic_name LIKE ? OR composition LIKE ? OR manufacturer LIKE ? OR category LIKE ?)"
        )
        params.extend([search_param, search_param, search_param, search_param, search_param])

    if category:
        query_conditions.append("category = ?")
        params.append(category)

    where_clause = " WHERE " + " AND ".join(query_conditions)

    # Total count
    count_sql = f"SELECT COUNT(*) as total FROM medicines {where_clause}"
    total = db.execute(count_sql, params).fetchone()["total"]

    # Paginated data
    data_sql = f"""
        SELECT id, name, generic_name, manufacturer, category, dosage_form, strength, composition, pack_size, mrp, requires_prescription, created_at
        FROM medicines
        {where_clause}
        ORDER BY name ASC
        LIMIT ? OFFSET ?
    """
    rows = db.execute(data_sql, params + [limit, offset]).fetchall()

    medicines = [
        {
            "id": r["id"],
            "name": r["name"],
            "generic_name": r["generic_name"],
            "composition": r["composition"] or r["generic_name"],
            "strength": r["strength"] or "Standard",
            "manufacturer": r["manufacturer"],
            "category": r["category"],
            "dosage_form": r["dosage_form"],
            "pack_size": r["pack_size"],
            "mrp": float(r["mrp"]),
            "requires_prescription": bool(r["requires_prescription"]),
            "created_at": r["created_at"]
        }
        for r in rows
    ]

    return jsonify({
        "medicines": medicines,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit if total > 0 else 1
        }
    }), 200


@medicine_bp.route("/<int:med_id>", methods=["GET"])
def get_medicine(med_id: int):
    db = get_db()
    row = db.execute(
        """
        SELECT id, name, generic_name, manufacturer, category, dosage_form, strength, composition, pack_size, mrp, requires_prescription, is_active, created_at
        FROM medicines
        WHERE id = ?
        """,
        (med_id,)
    ).fetchone()

    if not row:
        return jsonify({"error": "Medicine not found"}), 404

    return jsonify({
        "medicine": {
            "id": row["id"],
            "name": row["name"],
            "generic_name": row["generic_name"],
            "composition": row["composition"] or row["generic_name"],
            "strength": row["strength"] or "Standard",
            "manufacturer": row["manufacturer"],
            "category": row["category"],
            "dosage_form": row["dosage_form"],
            "pack_size": row["pack_size"],
            "mrp": float(row["mrp"]),
            "requires_prescription": bool(row["requires_prescription"]),
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"]
        }
    }), 200


@medicine_bp.route("", methods=["POST"])
@token_required
@role_required("ADMIN")
def create_medicine():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    raw_mrp = data.get("mrp")

    if not name:
        return jsonify({"error": "Medicine name is required"}), 400

    try:
        mrp = float(raw_mrp)
        if mrp <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Valid positive MRP is required"}), 400

    generic_name = (data.get("generic_name") or "").strip() or None
    manufacturer = (data.get("manufacturer") or "").strip() or None
    category = (data.get("category") or "General").strip() or "General"
    dosage_form = (data.get("dosage_form") or "").strip() or None
    pack_size = (data.get("pack_size") or "1 Unit").strip() or "1 Unit"
    requires_prescription = 1 if data.get("requires_prescription") else 0

    db = get_db()
    with transaction(db):
        cursor = db.execute(
            """
            INSERT INTO medicines (name, generic_name, manufacturer, category, dosage_form, pack_size, mrp, requires_prescription, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (name, generic_name, manufacturer, category, dosage_form, pack_size, mrp, requires_prescription)
        )
        med_id = cursor.lastrowid

    return jsonify({
        "message": "Medicine created successfully",
        "medicine": {
            "id": med_id,
            "name": name,
            "generic_name": generic_name,
            "manufacturer": manufacturer,
            "category": category,
            "dosage_form": dosage_form,
            "pack_size": pack_size,
            "mrp": mrp,
            "requires_prescription": bool(requires_prescription)
        }
    }), 201


@medicine_bp.route("/<int:med_id>", methods=["PUT"])
@token_required
@role_required("ADMIN")
def update_medicine(med_id: int):
    data = request.get_json() or {}
    db = get_db()
    existing = db.execute("SELECT id FROM medicines WHERE id = ?", (med_id,)).fetchone()
    if not existing:
        return jsonify({"error": "Medicine not found"}), 404

    name = (data.get("name") or "").strip()
    raw_mrp = data.get("mrp")

    if not name:
        return jsonify({"error": "Medicine name cannot be empty"}), 400

    try:
        mrp = float(raw_mrp)
        if mrp <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Valid positive MRP is required"}), 400

    generic_name = (data.get("generic_name") or "").strip() or None
    manufacturer = (data.get("manufacturer") or "").strip() or None
    category = (data.get("category") or "General").strip() or "General"
    dosage_form = (data.get("dosage_form") or "").strip() or None
    pack_size = (data.get("pack_size") or "1 Unit").strip() or "1 Unit"
    requires_prescription = 1 if data.get("requires_prescription") else 0
    is_active = 1 if data.get("is_active", True) else 0

    with transaction(db):
        db.execute(
            """
            UPDATE medicines
            SET name = ?, generic_name = ?, manufacturer = ?, category = ?,
                dosage_form = ?, pack_size = ?, mrp = ?, requires_prescription = ?, is_active = ?
            WHERE id = ?
            """,
            (name, generic_name, manufacturer, category, dosage_form, pack_size, mrp, requires_prescription, is_active, med_id)
        )

    return jsonify({"message": "Medicine updated successfully"}), 200


@medicine_bp.route("/<int:med_id>", methods=["DELETE"])
@token_required
@role_required("ADMIN")
def delete_medicine(med_id: int):
    db = get_db()
    existing = db.execute("SELECT id FROM medicines WHERE id = ?", (med_id,)).fetchone()
    if not existing:
        return jsonify({"error": "Medicine not found"}), 404

    with transaction(db):
        # Soft delete to preserve order history integrity
        db.execute("UPDATE medicines SET is_active = 0 WHERE id = ?", (med_id,))

    return jsonify({"message": "Medicine deactivated successfully"}), 200


@medicine_bp.route("/categories", methods=["GET"])
def get_categories():
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT category FROM medicines WHERE is_active = 1 AND category IS NOT NULL ORDER BY category ASC"
    ).fetchall()
    categories = [r["category"] for r in rows if r["category"]]
    return jsonify({"categories": categories}), 200


@medicine_bp.route("/import", methods=["POST"])
@token_required
@role_required("ADMIN")
def import_excel():
    """
    Validated Excel (.xlsx) file upload for catalogue bulk import/updates.
    Enforces format validation, positive MRP checks, and returns granular stats and error logs.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please upload a file with key 'file'"}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"error": "No file selected"}), 400

    filename = uploaded_file.filename.lower()
    if not filename.endswith(".xlsx"):
        return jsonify({"error": "Unsupported file format. Please upload an Excel (.xlsx) spreadsheet."}), 400

    try:
        file_bytes = BytesIO(uploaded_file.read())
        db = get_db()
        result = parse_and_validate_excel(file_bytes, db)
        return jsonify({
            "message": "Catalogue import processed",
            "stats": result
        }), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as exc:
        return jsonify({"error": f"Failed to process catalogue: {str(exc)}"}), 500


@medicine_bp.route("/template", methods=["GET"])
def download_template():
    """Returns downloadable starter .xlsx template for administrators."""
    stream = generate_catalogue_template()
    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="tapza_medicine_import_template.xlsx"
    )
