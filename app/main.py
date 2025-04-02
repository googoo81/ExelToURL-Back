from flask import Flask
from flask_cors import CORS

def create_app():
    """Initialize and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all endpoints
    
    # Import blueprints - ensure these match your actual file names
    from app.routes.url_route import url_bp  # Change from url_routes to url_route if that's your file name
    from app.routes.xml_route import xml_bp  # Change from xml_routes to xml_route if that's your file name
    
    app.register_blueprint(url_bp)
    app.register_blueprint(xml_bp)
    
    return app