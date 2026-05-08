from datetime import datetime
from app.extensions import db


class ImportedAsset(db.Model):
    __tablename__ = "imported_assets"

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)

    file_path = db.Column(db.String(500), nullable=False)

    file_type = db.Column(db.String(20), nullable=False)

    uploaded_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    metadata_json = db.Column(db.JSON, nullable=True)

    user = db.relationship(
        "User",
        backref="imported_assets",
        lazy=True
    )

    def __repr__(self):
        return f"<ImportedAsset {self.id} {self.original_filename}>"