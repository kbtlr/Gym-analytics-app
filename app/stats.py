from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from .extensions import db
from .models import BodyMetricEntry, Lift, Workout, WorkoutSet

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")

### Training Periodization Constants

# Volume multipliers per micro-week within a 4-week meso block.
# Week 1–3 = progressive accumulation; Week 4 = deload (~50 % of peak).
MICRO_WEEK_VOLUME_MULTIPLIERS = {1: 0.80, 2: 0.90, 3: 1.00, 4: 0.50}

# Meso-block intensity modifiers — later blocks push higher intensity /
# slightly lower raw volume as the macrocycle progresses toward a peak.
MESO_BLOCK_INTENSITY_MODIFIERS = {1: 1.00, 2: 1.05, 3: 1.10, 4: 1.15}

# Minimum recommended working sets per lift per week by experience level.
MIN_WEEKLY_SETS = {
    "beginner":     {"squat": 6,  "bench": 6,  "deadlift": 4},
    "intermediate": {"squat": 10, "bench": 10, "deadlift": 8},
    "advanced":     {"squat": 14, "bench": 14, "deadlift": 10},
}

# Maximum recoverable volume per lift per week by experience level.
MAX_WEEKLY_SETS = {
    "beginner":     {"squat": 12, "bench": 12, "deadlift": 8},
    "intermediate": {"squat": 20, "bench": 20, "deadlift": 16},
    "advanced":     {"squat": 26, "bench": 26, "deadlift": 20},
}

BIG_THREE_ALIASES = {
    "squat": {
        "squat", "back squat", "front squat", "pause squat",
        "high bar squat", "low bar squat", "safety bar squat",
    },
    "bench": {
        "bench", "bench press", "paused bench", "close grip bench",
        "incline bench", "flat bench",
    },
    "deadlift": {
        "deadlift", "conventional deadlift", "sumo deadlift",
        "paused deadlift", "romanian deadlift", "rdl", "trap bar deadlift",
    },
}


### Utility Helper Functions

def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _to_float(value, default=None):
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_name(value):
    return (value or "").strip().lower()


def _infer_big_three_bucket(exercise_name, movement_category=None):
    normalized_name = _normalize_name(exercise_name)
    normalized_category = _normalize_name(movement_category)

    if normalized_category in {"squat", "bench", "deadlift"}:
        return normalized_category

    for bucket, aliases in BIG_THREE_ALIASES.items():
        if normalized_name in aliases:
            return bucket
        if bucket in normalized_name:
            return bucket

    return None


def _estimate_e1rm(weight_kg, reps):
    """Epley formula: weight × (1 + reps / 30)."""
    if not weight_kg or not reps or reps <= 0:
        return 0.0
    return round(float(weight_kg) * (1 + float(reps) / 30.0), 2)


def _serialize_body_metric(entry):
    return {
        "id": entry.id,
        "recordedAt": entry.recorded_at.isoformat() if entry.recorded_at else None,
        "bodyWeightKg": entry.body_weight_kg,
        "bodyFatPercent": entry.body_fat_percent,
        "waistCm": entry.waist_cm,
        "chestCm": entry.chest_cm,
        "armCm": entry.arm_cm,
        "thighCm": entry.thigh_cm,
        "notes": entry.notes,
    }


def _serialize_set(workout_set):
    set_volume = round((workout_set.weight_kg or 0) * (workout_set.reps or 0), 2)
    e1rm = _estimate_e1rm(workout_set.weight_kg, workout_set.reps)
    return {
        "id": workout_set.id,
        "exerciseName": workout_set.exercise_name,
        "movementCategory": workout_set.movement_category,
        "variationName": workout_set.variation_name,
        "setType": workout_set.set_type,
        "reps": workout_set.reps,
        "weightKg": workout_set.weight_kg,
        "rpe": workout_set.rpe,
        "rir": workout_set.rir,
        "performedAt": workout_set.performed_at.isoformat() if workout_set.performed_at else None,
        "volumeKg": set_volume,
        "estimated1RMKg": e1rm,
    }


def _serialize_workout(workout):
    sets = sorted(workout.sets, key=lambda s: s.id)
    return {
        "id": workout.id,
        "performedAt": workout.performed_at.isoformat() if workout.performed_at else None,
        "totalVolumeKg": workout.total_volume_kg,
        "setCount": len(sets),
        "sets": [_serialize_set(s) for s in sets],
    }


def _get_cycle_data(user):
    """
    Returns a dict with macroWeek, mesoBlock, microWeek, totalWeeks,
    completionPercent, workoutsLogged — computed from the user's first workout.
    """
    total_weeks = user.program_length_weeks or 12
    workouts = (
        db.session.query(Workout).filter_by(user_id=user.id)
        .order_by(Workout.performed_at.asc(), Workout.id.asc())
        .all()
    )
    first_workout = workouts[0] if workouts else None

    if first_workout and first_workout.performed_at:
        days_elapsed = max((datetime.utcnow() - first_workout.performed_at).days, 0)
        macro_week = (days_elapsed // 7) + 1
    else:
        macro_week = 1

    macro_week = min(macro_week, total_weeks) if total_weeks > 0 else macro_week
    meso_block = ((macro_week - 1) // 4) + 1
    micro_week = ((macro_week - 1) % 4) + 1
    completion_percent = round((macro_week / total_weeks) * 100, 2) if total_weeks else 0.0

    return {
        "macroWeek": macro_week,
        "mesoBlock": meso_block,
        "microWeek": micro_week,
        "totalWeeks": total_weeks,
        "completionPercent": completion_percent,
        "workoutsLogged": len(workouts),
    }


def _build_volume_recommendation(user, cycle_data):
    """
    Returns per-lift volume recommendations for the current micro-week,
    adjusted for meso-block intensity progression and deload weeks.

    Logic:
      1. Determine base weekly sets from the user's experience level.
      2. Apply the micro-week multiplier (deload on week 4).
      3. Apply the meso-block intensity modifier (later blocks = slightly
         higher intensity, slightly lower raw volume).
      4. Clamp to [min, max] recoverable volume for the experience level.
      5. Compute a target volume in kg using the user's current best e1RM
         for each lift (sets × avg_reps_target × intensity_fraction_of_e1rm).
    """
    experience = _normalize_name(user.experience_level) or "intermediate"
    if experience not in MIN_WEEKLY_SETS:
        experience = "intermediate"

    micro_week = cycle_data["microWeek"]
    meso_block = cycle_data["mesoBlock"]
    is_deload = micro_week == 4

    volume_multiplier = MICRO_WEEK_VOLUME_MULTIPLIERS.get(micro_week, 1.0)
    intensity_modifier = MESO_BLOCK_INTENSITY_MODIFIERS.get(min(meso_block, 4), 1.15)

    # Fetch the user's current best e1RM per big-three lift
    lifts = db.session.query(Lift).filter_by(user_id=user.id).all()
    best_e1rm = {"squat": 0.0, "bench": 0.0, "deadlift": 0.0}
    for lift in lifts:
        bucket = _infer_big_three_bucket(lift.exercise_name, lift.movement_category)
        if bucket in best_e1rm:
            candidate = _estimate_e1rm(lift.best_weight_kg, lift.best_reps)
            if candidate > best_e1rm[bucket]:
                best_e1rm[bucket] = candidate

    recommendations = {}
    phase_label = _phase_label(micro_week, meso_block)

    for lift in ("squat", "bench", "deadlift"):
        base_sets = (MIN_WEEKLY_SETS[experience][lift] + MAX_WEEKLY_SETS[experience][lift]) / 2
        recommended_sets = round(base_sets * volume_multiplier)
        recommended_sets = max(
            MIN_WEEKLY_SETS[experience][lift],
            min(recommended_sets, MAX_WEEKLY_SETS[experience][lift]),
        )

        ### Target working weight as fraction of 1RM, adjusted for meso block progress
        ### Deload weeks use 60% 1RM; normal weeks progress from 70% up to 85%
        if is_deload:
            intensity_fraction = 0.60
        else:
            base_fraction = 0.70 + (micro_week - 1) * 0.05   # 0.70 → 0.80 over weeks 1–3
            intensity_fraction = min(base_fraction * intensity_modifier, 0.90)

        e1rm = best_e1rm[lift]
        target_weight_kg = round(e1rm * intensity_fraction, 1) if e1rm > 0 else None

        ### Rep scheme: deload uses higher reps, peak weeks use lower reps
        if is_deload:
            target_reps = 8
        else:
            target_reps = max(3, 8 - micro_week)   # week1=7, week2=6, week3=5

        target_volume_kg = (
            round(recommended_sets * target_reps * target_weight_kg, 1)
            if target_weight_kg
            else None
        )

        recommendations[lift] = {
            "recommendedSets": recommended_sets,
            "targetRepsPerSet": target_reps,
            "targetWeightKg": target_weight_kg,
            "targetVolumeKg": target_volume_kg,
            "intensityFraction": round(intensity_fraction, 3),
            "currentBestE1RMKg": e1rm if e1rm > 0 else None,
            "minSets": MIN_WEEKLY_SETS[experience][lift],
            "maxSets": MAX_WEEKLY_SETS[experience][lift],
        }

    return {
        "phase": phase_label,
        "microWeek": micro_week,
        "mesoBlock": meso_block,
        "isDeload": is_deload,
        "experienceLevel": experience,
        "lifts": recommendations,
    }


def _phase_label(micro_week, meso_block):
    if micro_week == 4:
        return "Deload"
    labels = {1: "Accumulation", 2: "Intensification", 3: "Peak"}
    base = labels.get(micro_week, "Accumulation")
    return f"Meso {meso_block} — {base}"


### Body Metrics Routes

@stats_bp.route("/body-metrics", methods=["GET", "POST"])
@login_required
def body_metrics():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}

        entry = BodyMetricEntry(
            user_id=current_user.id,
            body_weight_kg=_to_float(payload.get("bodyWeightKg")),
            body_fat_percent=_to_float(payload.get("bodyFatPercent")),
            waist_cm=_to_float(payload.get("waistCm")),
            chest_cm=_to_float(payload.get("chestCm")),
            arm_cm=_to_float(payload.get("armCm")),
            thigh_cm=_to_float(payload.get("thighCm")),
            notes=(payload.get("notes") or "").strip() or None,
        )

        recorded_at = _parse_datetime(payload.get("recordedAt"))
        if recorded_at:
            entry.recorded_at = recorded_at

        db.session.add(entry)
        db.session.commit()

        return jsonify({"message": "Body metrics logged", "entry": _serialize_body_metric(entry)}), 201

    entries = (
        db.session.query(BodyMetricEntry).filter_by(user_id=current_user.id)
        .order_by(BodyMetricEntry.recorded_at.asc(), BodyMetricEntry.id.asc())
        .all()
    )
    return jsonify({"data": [_serialize_body_metric(e) for e in entries]}), 200


@stats_bp.route("/body-metrics/latest", methods=["GET"])
@login_required
def latest_body_metrics():
    entry = (
        db.session.query(BodyMetricEntry).filter_by(user_id=current_user.id)
        .order_by(BodyMetricEntry.recorded_at.desc(), BodyMetricEntry.id.desc())
        .first()
    )
    return jsonify({"data": _serialize_body_metric(entry) if entry else None}), 200


@stats_bp.route("/body-metrics/summary", methods=["GET"])
@login_required
def body_metrics_summary():
    entries = (
        db.session.query(BodyMetricEntry).filter_by(user_id=current_user.id)
        .order_by(BodyMetricEntry.recorded_at.asc(), BodyMetricEntry.id.asc())
        .all()
    )

    latest = entries[-1] if entries else None
    previous = entries[-2] if len(entries) > 1 else None

    def _diff(a, b, field):
        va = getattr(a, field, None)
        vb = getattr(b, field, None)
        if va is not None and vb is not None:
            return round(va - vb, 2)
        return None

    summary = {
        "latest": _serialize_body_metric(latest) if latest else None,
        "changeFromPrevious": {
            "bodyWeightKg": _diff(latest, previous, "body_weight_kg") if latest and previous else None,
            "bodyFatPercent": _diff(latest, previous, "body_fat_percent") if latest and previous else None,
            "waistCm": _diff(latest, previous, "waist_cm") if latest and previous else None,
        },
        "entryCount": len(entries),
    }
    return jsonify({"data": summary}), 200


### Volume Tracking Routes

@stats_bp.route("/volume", methods=["GET"])
@login_required
def volume_over_time():
    lift_filter = _normalize_name(request.args.get("lift"))
    days = _to_int(request.args.get("days"), default=90)

    workouts = (
        db.session.query(Workout).filter_by(user_id=current_user.id)
        .order_by(Workout.performed_at.asc(), Workout.id.asc())
        .all()
    )

    if days and days > 0:
        cutoff = datetime.utcnow() - timedelta(days=days)
        workouts = [w for w in workouts if w.performed_at and w.performed_at >= cutoff]

    data = []
    for workout in workouts:
        total_volume = workout.total_volume_kg or 0.0

        if lift_filter:
            total_volume = 0.0
            for s in workout.sets:
                bucket = _infer_big_three_bucket(s.exercise_name, s.movement_category)
                if bucket == lift_filter:
                    total_volume += (s.weight_kg or 0) * (s.reps or 0)

        data.append({
            "date": workout.performed_at.date().isoformat() if workout.performed_at else None,
            "performedAt": workout.performed_at.isoformat() if workout.performed_at else None,
            "lift": lift_filter or "all",
            "totalVolumeKg": round(total_volume, 2),
            "workoutId": workout.id,
        })

    return jsonify({"data": data}), 200


@stats_bp.route("/volume/big-three", methods=["GET"])
@login_required
def big_three_volume():
    workouts = (
        db.session.query(Workout).filter_by(user_id=current_user.id)
        .order_by(Workout.performed_at.asc(), Workout.id.asc())
        .all()
    )

    data = []
    for workout in workouts:
        totals = {"squat": 0.0, "bench": 0.0, "deadlift": 0.0}
        for s in workout.sets:
            bucket = _infer_big_three_bucket(s.exercise_name, s.movement_category)
            if bucket in totals:
                totals[bucket] += (s.weight_kg or 0) * (s.reps or 0)

        data.append({
            "date": workout.performed_at.date().isoformat() if workout.performed_at else None,
            "performedAt": workout.performed_at.isoformat() if workout.performed_at else None,
            "workoutId": workout.id,
            "squatVolumeKg": round(totals["squat"], 2),
            "benchVolumeKg": round(totals["bench"], 2),
            "deadliftVolumeKg": round(totals["deadlift"], 2),
        })

    return jsonify({"data": data}), 200


### Personal Best Tracking Routes

@stats_bp.route("/personal-bests", methods=["GET"])
@login_required
def personal_bests():
    lifts = (
        db.session.query(Lift).filter_by(user_id=current_user.id)
        .order_by(Lift.exercise_name.asc())
        .all()
    )

    data = []
    for lift in lifts:
        weight = lift.best_weight_kg or 0.0
        reps = lift.best_reps or 0
        data.append({
            "exercise": lift.exercise_name,
            "movementCategory": lift.movement_category,
            "variationName": lift.variation_name,
            "weightKg": weight,
            "reps": reps,
            "estimated1RMKg": _estimate_e1rm(weight, reps),
            "recordedAt": lift.recorded_at.isoformat() if lift.recorded_at else None,
        })

    return jsonify({"data": data}), 200


@stats_bp.route("/personal-bests/big-three", methods=["GET"])
@login_required
def big_three_personal_bests():
    lifts = db.session.query(Lift).filter_by(user_id=current_user.id).all()

    summary = {"squat": None, "bench": None, "deadlift": None}

    for lift in lifts:
        bucket = _infer_big_three_bucket(lift.exercise_name, lift.movement_category)
        if not bucket:
            continue

        current_best = summary[bucket]
        candidate_e1rm = _estimate_e1rm(lift.best_weight_kg, lift.best_reps)
        current_e1rm = current_best["estimated1RMKg"] if current_best else 0.0

        if current_best is None or candidate_e1rm > current_e1rm:
            summary[bucket] = {
                "exercise": lift.exercise_name,
                "movementCategory": lift.movement_category,
                "variationName": lift.variation_name,
                "weightKg": lift.best_weight_kg,
                "reps": lift.best_reps,
                "estimated1RMKg": candidate_e1rm,
                "recordedAt": lift.recorded_at.isoformat() if lift.recorded_at else None,
            }

    return jsonify({"data": summary}), 200


### Training Cycle & Recommendation Routes

@stats_bp.route("/cycle-progress", methods=["GET"])
@login_required
def cycle_progress():
    data = _get_cycle_data(current_user)
    return jsonify({"data": data}), 200


@stats_bp.route("/volume-recommendation", methods=["GET"])
@login_required
def volume_recommendation():
    """
    Returns periodization-aware volume and intensity targets for the current
    micro-week, adjusted for meso-block progression and deload scheduling.

    Response shape:
    {
      "data": {
        "phase": "Meso 2 — Intensification",
        "microWeek": 2,
        "mesoBlock": 2,
        "isDeload": false,
        "experienceLevel": "intermediate",
        "lifts": {
          "squat":    { recommendedSets, targetRepsPerSet, targetWeightKg,
                        targetVolumeKg, intensityFraction, currentBestE1RMKg,
                        minSets, maxSets },
          "bench":    { ... },
          "deadlift": { ... }
        }
      }
    }
    """
    cycle_data = _get_cycle_data(current_user)
    recommendation = _build_volume_recommendation(current_user, cycle_data)
    return jsonify({"data": recommendation}), 200


### Workout Logging Routes

@stats_bp.route("/workouts", methods=["GET"])
@login_required
def workout_history():
    workouts = (
        db.session.query(Workout).filter_by(user_id=current_user.id)
        .order_by(Workout.performed_at.desc(), Workout.id.desc())
        .all()
    )
    return jsonify({"data": [_serialize_workout(w) for w in workouts]}), 200


@stats_bp.route("/workout", methods=["POST"])
@login_required
def log_workout():
    payload = request.get_json(silent=True) or {}
    sets_payload = payload.get("sets") or []

    if not isinstance(sets_payload, list) or not sets_payload:
        return jsonify({"message": "Workout must include at least one set"}), 400

    workout = Workout(user_id=current_user.id)
    performed_at = _parse_datetime(payload.get("performedAt"))
    if performed_at:
        workout.performed_at = performed_at

    db.session.add(workout)
    db.session.flush()

    total_volume = 0.0
    personal_best_updates = []

    for raw_set in sets_payload:
        exercise_name = (raw_set.get("exerciseName") or "").strip()
        reps = _to_int(raw_set.get("reps"))
        weight_kg = _to_float(raw_set.get("weightKg"))

        if not exercise_name or reps is None or reps <= 0 or weight_kg is None or weight_kg < 0:
            db.session.rollback()
            return jsonify({"message": "Each set requires exerciseName, reps, and weightKg"}), 400

        movement_category = raw_set.get("movementCategory") or _infer_big_three_bucket(exercise_name)
        variation_name = raw_set.get("variationName")
        set_type = raw_set.get("setType") or "working"

        workout_set = WorkoutSet(
            workout_id=workout.id,
            exercise_name=exercise_name,
            movement_category=movement_category,
            variation_name=(variation_name or "").strip() or None,
            set_type=(set_type or "").strip() or "working",
            reps=reps,
            weight_kg=weight_kg,
            rpe=_to_float(raw_set.get("rpe")),
            rir=_to_int(raw_set.get("rir")),
        )

        set_performed_at = _parse_datetime(raw_set.get("performedAt"))
        if set_performed_at:
            workout_set.performed_at = set_performed_at
        elif performed_at:
            workout_set.performed_at = performed_at

        db.session.add(workout_set)
        set_volume = weight_kg * reps
        total_volume += set_volume

        ### Automatically check and update personal best records
        lift = db.session.query(Lift).filter_by(user_id=current_user.id, exercise_name=exercise_name).first()
        is_new_pb = False

        if not lift:
            lift = Lift(
                user_id=current_user.id,
                exercise_name=exercise_name,
                movement_category=movement_category,
                variation_name=(variation_name or "").strip() or None,
                best_weight_kg=weight_kg,
                best_reps=reps,
            )
            if set_performed_at:
                lift.recorded_at = set_performed_at
            elif performed_at:
                lift.recorded_at = performed_at
            db.session.add(lift)
            is_new_pb = True
        else:
            existing_weight = lift.best_weight_kg or 0.0
            existing_reps = lift.best_reps or 0
            if weight_kg > existing_weight or (weight_kg == existing_weight and reps > existing_reps):
                lift.best_weight_kg = weight_kg
                lift.best_reps = reps
                lift.movement_category = movement_category
                lift.variation_name = (variation_name or "").strip() or lift.variation_name
                if set_performed_at:
                    lift.recorded_at = set_performed_at
                elif performed_at:
                    lift.recorded_at = performed_at
                is_new_pb = True

        if is_new_pb:
            personal_best_updates.append({
                "exercise": exercise_name,
                "weightKg": weight_kg,
                "reps": reps,
                "estimated1RMKg": _estimate_e1rm(weight_kg, reps),
            })

    workout.total_volume_kg = round(total_volume, 2)
    db.session.commit()

    return jsonify({
        "message": "Workout logged successfully",
        "workout": _serialize_workout(workout),
        "personalBestUpdates": personal_best_updates,
    }), 201


### Dashboard Summary Routes

@stats_bp.route("/dashboard-summary", methods=["GET"])
@login_required
def dashboard_summary():
    latest_metrics = (
        db.session.query(BodyMetricEntry).filter_by(user_id=current_user.id)
        .order_by(BodyMetricEntry.recorded_at.desc(), BodyMetricEntry.id.desc())
        .first()
    )
    latest_workout = (
        db.session.query(Workout).filter_by(user_id=current_user.id)
        .order_by(Workout.performed_at.desc(), Workout.id.desc())
        .first()
    )
    workouts = db.session.query(Workout).filter_by(user_id=current_user.id).all()
    recent_volume = round(
        sum((w.total_volume_kg or 0.0) for w in workouts[-7:]), 2
    ) if workouts else 0.0

    cycle_data = _get_cycle_data(current_user)
    recommendation = _build_volume_recommendation(current_user, cycle_data)

    # Big-three personal bests
    lifts = db.session.query(Lift).filter_by(user_id=current_user.id).all()
    big_three_pbs = {"squat": None, "bench": None, "deadlift": None}
    for lift in lifts:
        bucket = _infer_big_three_bucket(lift.exercise_name, lift.movement_category)
        if not bucket:
            continue
        candidate_e1rm = _estimate_e1rm(lift.best_weight_kg, lift.best_reps)
        current = big_three_pbs[bucket]
        if current is None or candidate_e1rm > current["estimated1RMKg"]:
            big_three_pbs[bucket] = {
                "exercise": lift.exercise_name,
                "weightKg": lift.best_weight_kg,
                "reps": lift.best_reps,
                "estimated1RMKg": candidate_e1rm,
                "recordedAt": lift.recorded_at.isoformat() if lift.recorded_at else None,
            }

    return jsonify({
        "data": {
            "latestBodyMetrics": _serialize_body_metric(latest_metrics) if latest_metrics else None,
            "latestWorkout": _serialize_workout(latest_workout) if latest_workout else None,
            "recentVolumeKg": recent_volume,
            "bigThreePersonalBests": big_three_pbs,
            "cycleProgress": cycle_data,
            "volumeRecommendation": recommendation,
        }
    }), 200
