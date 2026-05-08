from flask import Flask
from app.extensions import db, migrate
from app.routes.prompts import prompts_bp
from app.routes.auth import auth_bp
from app.routes.assets import assets_bp
from flask_cors import CORS

from app.models.user import User
from app.models.prompt import PromptRequest
from app.models.feedback import GenerationFeedback
from app.models.imported_asset import ImportedAsset





def create_app():
    app = Flask(__name__)


    CORS(
    app,
    supports_credentials=True,
    origins=["http://127.0.0.1:3000", "http://localhost:3000"]
    )


    app.config.from_object("config.Config")
    db.init_app(app)
    migrate.init_app(app, db)


    app.register_blueprint(prompts_bp, url_prefix="/prompts")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(assets_bp, url_prefix="/assets")


    @app.route("/")
    def home():
        return "API is running"


    return app
