from flask import Blueprint, request, jsonify, g, current_app
from app.db import get_db, transaction
from app.utils.auth_helpers import (
    hash_password,
    verify_password,
    generate_jwt,
    token_required
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role = (data.get("role") or "").strip().upper()
    phone = (data.get("phone") or "").strip()
    zone = (data.get("zone") or "").strip().upper()

    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not full_name:
        return jsonify({"error": "Full name is required"}), 400
    if role not in ("CUSTOMER", "PHARMACY"):
        return jsonify({"error": "Role must be CUSTOMER or PHARMACY"}), 400
    if not zone:
        return jsonify({"error": "Zone is required (e.g., ZONE_A, ZONE_B, CENTRAL)"}), 400

    pharmacy_name = (data.get("pharmacy_name") or "").strip()
    license_number = (data.get("license_number") or "").strip()
    address = (data.get("address") or "").strip()

    if role == "PHARMACY":
        if not pharmacy_name or not license_number or not address:
            return jsonify({
                "error": "Pharmacies require pharmacy_name, license_number, and address"
            }), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "An account with this email already exists"}), 409

    pwd_hash = hash_password(password)

    try:
        with transaction(db):
            cursor = db.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role, phone, zone)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, pwd_hash, full_name, role, phone, zone)
            )
            user_id = cursor.lastrowid

            pharmacy_data = None
            if role == "PHARMACY":
                from app.services.geo_service import geocode_address
                p_lat = data.get("latitude")
                p_lon = data.get("longitude")
                if p_lat is None or p_lon is None:
                    p_lat, p_lon, _ = geocode_address(address)

                db.execute(
                    """
                    INSERT INTO pharmacy_profiles (user_id, pharmacy_name, license_number, address, zone, is_active, latitude, longitude, phone)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                    """,
                    (user_id, pharmacy_name, license_number, address, zone, p_lat, p_lon, phone)
                )
                db.execute(
                    """
                    INSERT OR REPLACE INTO pharmacy_rtree (id, min_lat, max_lat, min_lng, max_lng)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, p_lat, p_lat, p_lon, p_lon)
                )
                pharmacy_data = {
                    "pharmacy_name": pharmacy_name,
                    "license_number": license_number,
                    "address": address,
                    "zone": zone,
                    "latitude": p_lat,
                    "longitude": p_lon,
                    "is_active": True
                }

        token = generate_jwt({
            "user_id": user_id,
            "email": email,
            "role": role,
            "zone": zone
        }, current_app.config["JWT_SECRET"])

        return jsonify({
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": role,
                "phone": phone,
                "zone": zone,
                "pharmacy": pharmacy_data
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to register user: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Email or Username and password are required"}), 400

    db = get_db()
    # Check matching either email or username or email alias
    user = db.execute(
        """
        SELECT id, email, username, password_hash, full_name, role, phone, zone
        FROM users
        WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)
        """,
        (identifier, identifier, f"{identifier}@tapza.com")
    ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    pharmacy_data = None
    if user["role"] == "PHARMACY":
        profile = db.execute(
            "SELECT pharmacy_name, license_number, address, zone, is_active FROM pharmacy_profiles WHERE user_id = ?",
            (user["id"],)
        ).fetchone()
        if profile:
            pharmacy_data = {
                "pharmacy_name": profile["pharmacy_name"],
                "license_number": profile["license_number"],
                "address": profile["address"],
                "zone": profile["zone"],
                "is_active": bool(profile["is_active"])
            }

    token = generate_jwt({
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "zone": user["zone"]
    }, current_app.config["JWT_SECRET"])

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "phone": user["phone"],
            "zone": user["zone"],
            "pharmacy": pharmacy_data
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user():
    db = get_db()
    user = db.execute(
        "SELECT id, email, full_name, role, phone, zone, created_at FROM users WHERE id = ?",
        (g.user_id,)
    ).fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    pharmacy_data = None
    if user["role"] == "PHARMACY":
        profile = db.execute(
            "SELECT pharmacy_name, license_number, address, zone, is_active FROM pharmacy_profiles WHERE user_id = ?",
            (user["id"],)
        ).fetchone()
        if profile:
            pharmacy_data = {
                "pharmacy_name": profile["pharmacy_name"],
                "license_number": profile["license_number"],
                "address": profile["address"],
                "zone": profile["zone"],
                "is_active": bool(profile["is_active"])
            }

    return jsonify({
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "phone": user["phone"],
            "zone": user["zone"],
            "created_at": user["created_at"],
            "pharmacy": pharmacy_data
        }
    }), 200
