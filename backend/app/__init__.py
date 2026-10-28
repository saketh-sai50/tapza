import time
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.db import init_db, close_db
from app.routes.auth_routes import auth_bp
from app.routes.medicine_routes import medicine_bp
from app.routes.order_routes import order_bp, notification_bp
from app.routes.quote_routes import quote_bp
from app.routes.selection_routes import selection_bp
from app.routes.pharmacy_routes import pharmacy_bp
from app.routes.admin_routes import admin_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for frontend applications (web & native)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Database teardown
    app.teardown_appcontext(close_db)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(medicine_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(quote_bp)
    app.register_blueprint(selection_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(admin_bp)

    # Serve Interactive Test Web UI
    @app.route("/", methods=["GET"])
    def index():
        return app.send_static_file("index.html")

    # System Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Tapza Backend API",
            "broadcast_window_seconds": app.config["BROADCAST_WINDOW_SECONDS"],
            "server_time": int(time.time())
        }), 200

    # Initialize schema & default admin
    with app.app_context():
        init_db(app)

    return app
