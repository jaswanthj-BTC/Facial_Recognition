from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config, DatabaseConfig, init_database
from routes.auth import auth_bp


# Import detection routes (will be created by Person C)
# from routes.detection import detection_bp


def create_app():
    """
    Application Factory Pattern
    Creates and configures the Flask application
    """

    # Initialize Flask app
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Initialize JWT
    jwt = JWTManager(app)

    # Test database connection
    if not DatabaseConfig.test_connection():
        print("⚠️ Warning: Could not connect to MongoDB. Check your MONGO_URI in .env")
    else:
        # Initialize database (create indexes)
        init_database()

    # Register Blueprints (route modules)
    app.register_blueprint(auth_bp)

    # app.register_blueprint(detection_bp)  # Uncomment when Person C creates this

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Facial Tracker API',
            'version': '1.0',
            'status': 'running',
            'endpoints': {
                'auth': '/api/auth',
                'detection': '/api/detection'
            }
        })

    # Health check endpoint
    @app.route('/health')
    def health():
        db_status = DatabaseConfig.test_connection()
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'database': 'connected' if db_status else 'disconnected'
        }), 200 if db_status else 503

    # JWT error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            'success': False,
            'message': 'Missing authorization token'
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has expired'
        }), 401

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

    return app


# Run the application
if __name__ == '__main__':
    app = create_app()

    print("\n" + "=" * 50)
    print("🚀 Facial Tracker Backend Server")
    print("=" * 50)
    print(f"📍 Running on: http://{Config.HOST}:{Config.PORT}")
    print(f"🔧 Environment: {'Development' if Config.DEBUG else 'Production'}")
    print(f"🗄️  Database: MongoDB")
    print("=" * 50 + "\n")

    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        DatabaseConfig.close_connection()