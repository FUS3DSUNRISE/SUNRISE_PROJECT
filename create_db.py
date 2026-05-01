from app import create_app, db
from app.models.prompt import PromptRequest
from app.models.user import User
from app.models.feedback import GenerationFeedback
import os

app = create_app()

with app.app_context():
    print("Instance path:", app.instance_path)
    print("Database URI:", app.config["SQLALCHEMY_DATABASE_URI"])
    db.drop_all()
    db.create_all()
    print("Database created successfully.")