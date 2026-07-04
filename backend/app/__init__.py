from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    # Allow all origins for now — restrict to the Vercel frontend URL once deployed.
    CORS(app, origins="*")

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
