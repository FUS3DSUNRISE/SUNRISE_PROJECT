from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash


from app.extensions import db
from app.models.user import User


auth_bp = Blueprint("auth", __name__)




@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()


    if not data:
        return jsonify({"error": "Missing JSON body"}), 400


    email = data.get("email", "").strip()
    password = data.get("password", "").strip()


    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400


    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already in use"}), 409


    # maybe change this later
    username = email.split("@")[0]


    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1


    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )


    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id


    return jsonify({
        "message": "Signup successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 201




@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()


    if not data:
        return jsonify({"error": "Missing JSON body"}), 400


    email = data.get("email", "").strip()
    password = data.get("password", "").strip()


    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400


    user = User.query.filter_by(email=email).first()


    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401


    session["user_id"] = user.id
    print("DEBUG login session user_id:", session.get("user_id"))


    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401


    user = User.query.get(user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "User not found"}), 404


    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200




@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logout successful"}), 200
