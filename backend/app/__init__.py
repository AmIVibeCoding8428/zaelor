from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    # Production, local frontend dev, and Vercel branch/preview deployments
    # (e.g. https://zaelor-git-some-branch-<team>.vercel.app). flask-cors
    # matches any origin string containing regex metacharacters via re.match,
    # so the wildcard entry below is a real (anchored) regex, not a glob.
    CORS(app, origins=[
        "https://zaelor.vercel.app",
        "http://localhost:5173",
        r"^https://zaelor-[\w-]+\.vercel\.app$",
    ])

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
