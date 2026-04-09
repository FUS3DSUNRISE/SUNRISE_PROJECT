from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)

    prompts = db.relationship("PromptRequest", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.id} {self.username}>"