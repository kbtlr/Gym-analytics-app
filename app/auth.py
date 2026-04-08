from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Called when the user clicks Confirm on the Login page.
    Expects JSON: { "username": "...", "password": "..." }
    Returns: 200 + user data on success, 401 on bad credentials.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # TODO: query User by username, verify password hash, call login_user(user)
    # Example:
    #   user = User.query.filter_by(username=username).first()
    #   if not user or not check_password_hash(user.password_hash, password):
    #       return jsonify({"error": "Invalid credentials"}), 401
    #   login_user(user)
    #   return jsonify({"message": "Logged in", "username": user.username}), 200

    return jsonify({"message": "login skeleton – not yet implemented"}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Called when the user clicks Log out on the Home page.
    """
    # TODO: logout_user()
    return jsonify({"message": "logout skeleton – not yet implemented"}), 200


@auth_bp.route("/register/step1", methods=["POST"])
def register_step1():
    """
    Called when the user continues from InformationSection (step 1).
    Expects JSON: { "email": "...", "username": "...", "password": "...", "confirmPassword": "..." }
    Validates input and creates the User row (without profile metrics yet).
    Returns: 201 on success, 400 on validation error.
    """
    data = request.get_json()
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    confirm_password = data.get("confirmPassword")

    # TODO: validate fields, check passwords match, check email/username not taken
    # TODO: hash password with generate_password_hash(password)
    # TODO: create User(email=email, username=username, password_hash=hashed)
    # TODO: db.session.add(user); db.session.commit()
    # TODO: return the new user's id so the frontend can pass it to step 2

    return jsonify({"message": "register step1 skeleton – not yet implemented"}), 201


@auth_bp.route("/register/step2", methods=["POST"])
def register_step2():
    """
    Called when the user continues from InformationSection2 (step 2).
    Expects JSON: {
        "userId": 1,
        "experienceLevel": "beginner",
        "programLengthWeeks": 12,
        "targetWeeklySets": 20,
        "lifts": [{ "exerciseName": "Squat", "bestWeightKg": 100, "bestReps": 5 }]
    }
    Saves profile metrics and initial lift baselines.
    Returns: 200 on success.
    """
    data = request.get_json()

    # TODO: fetch User by data["userId"]
    # TODO: update experience_level, program_length_weeks, target_weekly_sets
    # TODO: bulk-insert Lift rows from data["lifts"]
    # TODO: db.session.commit()

    return jsonify({"message": "register step2 skeleton – not yet implemented"}), 200
