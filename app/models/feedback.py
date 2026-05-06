from datetime import datetime
from app.extensions import db
import enum


class FeedbackRating(enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class GenerationFeedback(db.Model):
    __tablename__ = "generation_feedback"

    id = db.Column(db.Integer, primary_key=True)

    prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("prompt_requests.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    rating = db.Column(db.Enum(FeedbackRating), nullable=False)

    accuracy_score = db.Column(db.Integer, nullable=True)  # 1 to 5
    quality_score = db.Column(db.Integer, nullable=True)   # 1 to 5

    comment = db.Column(db.Text, nullable=True)

    llm_output = db.Column(db.Text, nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    result_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    prompt = db.relationship("PromptRequest", backref="feedbacks", lazy=True)
    user = db.relationship("User", backref="generation_feedbacks", lazy=True)

    def __repr__(self):
        return f"<GenerationFeedback {self.id}>"