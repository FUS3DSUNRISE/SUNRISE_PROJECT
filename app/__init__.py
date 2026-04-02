from flask import Flask
from app.routes.prompts import prompts_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    app.register_blueprint(prompts_bp, url_prefix="/prompts")

    @app.route("/")
    def home():
        return "API is running"

    return app