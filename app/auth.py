from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db
from .models import User, Lift, BodyMetricEntry

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Expects JSON: { "username": "...", "password": "..." }
    Returns 200 + user data on success, 401 on bad credentials.
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    login_user(user)
    return jsonify({
        "message": "Logged in successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "experienceLevel": user.experience_level,
            "programLengthWeeks": user.program_length_weeks,
            "targetWeeklySets": user.target_weekly_sets,
        }
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logs out the current user and clears the session."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/register/step1", methods=["POST"])
def register_step1():
    """
    Step 1: create the account credentials.
    Expects JSON: { "email": "...", "username": "...", "password": "...", "confirmPassword": "..." }
    Returns 201 + new user id on success.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirmPassword") or ""

    ### Validate required input fields
    if not email or not username or not password:
        return jsonify({"error": "Email, username, and password are required"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    ### Verify that email and username are available
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists"}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "That username is already taken"}), 409

    user = User(
        email=email,
        username=username,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created", "userId": user.id}), 201


@auth_bp.route("/register/step2", methods=["POST"])
def register_step2():
    """
    Step 2: save training profile and initial lift baselines.
    Expects JSON: {
        "userId": 1,
        "experienceLevel": "beginner",
        "programLengthWeeks": 12,
        "targetWeeklySets": 20,
        "startingBodyweightKg": 82.5,
        "lifts": [
            { "exerciseName": "Squat", "bestWeightKg": 140, "bestReps": 1 },
            { "exerciseName": "Bench Press", "bestWeightKg": 100, "bestReps": 1 },
            { "exerciseName": "Deadlift", "bestWeightKg": 180, "bestReps": 1 }
        ]
    }
    """
    data = request.get_json() or {}
    
    user_id = data.get("userId")
    if user_id is None or user_id == '':
        return jsonify({"error": "userId is required"}), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "userId must be a valid number"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    ### Save user training profile preferences
    user.experience_level = (data.get("experienceLevel") or "").strip() or None
    user.program_length_weeks = int(data["programLengthWeeks"]) if data.get("programLengthWeeks") else 12
    user.target_weekly_sets = int(data["targetWeeklySets"]) if data.get("targetWeeklySets") else None

    ### Record starting bodyweight if provided
    starting_bw = data.get("startingBodyweightKg")
    if starting_bw:
        try:
            bw_float = float(starting_bw)
            entry = BodyMetricEntry(user_id=user.id, body_weight_kg=bw_float)
            db.session.add(entry)
        except (TypeError, ValueError):
            pass

    ### Record initial lift personal bests
    lifts_payload = data.get("lifts") or []
    for raw in lifts_payload:
        exercise_name = (raw.get("exerciseName") or "").strip()
        if not exercise_name:
            continue
        try:
            weight_kg = float(raw["bestWeightKg"]) if raw.get("bestWeightKg") else None
            best_reps = int(raw["bestReps"]) if raw.get("bestReps") else None
        except (TypeError, ValueError):
            continue

        ### Only add if this user doesn't already have a record for this exercise
        existing = Lift.query.filter_by(user_id=user.id, exercise_name=exercise_name).first()
        if not existing:
            lift = Lift(
                user_id=user.id,
                exercise_name=exercise_name,
                best_weight_kg=weight_kg,
                best_reps=best_reps,
            )
            db.session.add(lift)

    db.session.commit()
    login_user(user)

    db.session.commit()

    resp = jsonify({
        "message": "Profile saved",
        "user": {
            "id": user.id,
            "username": user.username,
            "experienceLevel": user.experience_level,
            "programLengthWeeks": user.program_length_weeks,
            "targetWeeklySets": user.target_weekly_sets,
        }
    })
    
    login_user(user, remember=True)
    return resp, 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """Returns the currently authenticated user's profile."""
    return jsonify({
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "experienceLevel": current_user.experience_level,
            "programLengthWeeks": current_user.program_length_weeks,
            "targetWeeklySets": current_user.target_weekly_sets,
        }
    }), 200
