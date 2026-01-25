from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Import and register blueprints
    from app.routes import user_bp, internal_bp
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(internal_bp, url_prefix='/internal')
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'user-service'}
    
    return app
