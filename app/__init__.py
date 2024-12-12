from flask import Flask
from google.cloud import firestore

# Inisialisasi Firestore
firestore_client = firestore.Client()

def create_app():
    app = Flask(__name__)

    # Register blueprint
    from app.routes.recommend import recommend_blueprint
    from app.routes.optimize import optimize_route_blueprint

    app.register_blueprint(recommend_blueprint)
    app.register_blueprint(optimize_route_blueprint)

    return app
