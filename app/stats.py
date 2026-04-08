from flask import Blueprint, jsonify
from flask_login import login_required, current_user

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/volume", methods=["GET"])
@login_required
def volume_over_time():
    """
    Powers the 'Total Volume over Time' chart on the Home page.
    Returns a list of { date, totalVolumeKg } data points for the current user.
    """
    # TODO: query Workout rows for current_user.id, ordered by performed_at
    # TODO: return [{"date": w.performed_at.isoformat(), "totalVolumeKg": w.total_volume_kg} for w in workouts]

    return jsonify({"data": [], "message": "volume skeleton – not yet implemented"}), 200


@stats_bp.route("/personal-bests", methods=["GET"])
@login_required
def personal_bests():
    """
    Powers the 'Your Current Personal Bests' panel on the Home page.
    Returns the best weight * reps for each exercise logged by the user.
    """
    # TODO: query Lift rows for current_user.id
    # TODO: return [{"exercise": l.exercise_name, "weightKg": l.best_weight_kg, "reps": l.best_reps} for l in lifts]

    return jsonify({"data": [], "message": "personal bests skeleton – not yet implemented"}), 200


@stats_bp.route("/cycle-progress", methods=["GET"])
@login_required
def cycle_progress():
    """
    Powers the 'Current Cycle Progress' panel on the Home page.
    Returns macro / meso / micro cycle position for the current user.
    """
    # TODO: calculate week number within the user's program_length_weeks
    # TODO: derive meso and micro block from that
    # TODO: return { "macroWeek": 3, "mesoBlock": 1, "microWeek": 3, "totalWeeks": 12 }

    return jsonify({"data": {}, "message": "cycle progress skeleton – not yet implemented"}), 200


@stats_bp.route("/workout", methods=["POST"])
@login_required
def log_workout():
    """
    Logs a completed workout and updates volume + personal bests.
    Expects JSON: {
        "sets": [{ "exerciseName": "Bench Press", "reps": 5, "weightKg": 80 }]
    }
    """
    # TODO: create Workout row
    # TODO: create WorkoutSet rows, sum total_volume_kg
    # TODO: update Lift rows if any sets are new PBs
    # TODO: db.session.commit()

    return jsonify({"message": "log workout skeleton – not yet implemented"}), 201
