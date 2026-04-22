from datetime import datetime
from app.extensions import db
import enum


class PromptStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PromptRequest(db.Model):
    __tablename__ = "prompt_requests"

    id = db.Column(db.Integer, primary_key=True)
    prompt_text = db.Column(db.String(255), nullable=False)
    parameters = db.Column(db.JSON, nullable=True)
    generated_code = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    modification_command = db.Column(db.Text, nullable=True)

    status = db.Column(db.Enum(PromptStatus), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    result_path = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    parent_prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("prompt_requests.id"),
        nullable=True
    )

    parent_prompt = db.relationship(
        "PromptRequest",
        remote_side=[id],
        backref="refined_versions",
        lazy=True
    )

    def __repr__(self):
        return f"<PromptRequest {self.id}>"