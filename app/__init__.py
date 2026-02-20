import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Ensure data directories exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PDF_FOLDER'],
                   app.config['TEMPLATE_DIR']]:
        os.makedirs(folder, exist_ok=True)

    # Register blueprints
    from app.routes.admin import admin_bp
    from app.routes.estimator import estimator_bp
    from app.routes.api import api_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(estimator_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create tables
    with app.app_context():
        db.create_all()

    return app
