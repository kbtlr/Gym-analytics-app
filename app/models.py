from flask_login import UserMixin
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Step-2 registration fields
    experience_level = db.Column(db.String(50))        # beginner / intermediate / advanced
    program_length_weeks = db.Column(db.Integer)        # total macrocycle length
    target_weekly_sets = db.Column(db.Integer)          # aspiring weekly set volume

    # Relationships
    lifts = db.relationship("Lift", backref="user", lazy=True)
    workouts = db.relationship("Workout", backref="user", lazy=True)
    body_metrics = db.relationship("BodyMetricEntry", backref="user", lazy=True)

    def __init__(self, email, username, password_hash, **kwargs):
        super().__init__(**kwargs)
        self.email = email
        self.username = username
        self.password_hash = password_hash


class BodyMetricEntry(db.Model):
    """A single body-composition snapshot for a user."""
    __tablename__ = "body_metric_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recorded_at = db.Column(db.DateTime, server_default=db.func.now())

    body_weight_kg = db.Column(db.Float)
    body_fat_percent = db.Column(db.Float)
    waist_cm = db.Column(db.Float)
    chest_cm = db.Column(db.Float)
    arm_cm = db.Column(db.Float)
    thigh_cm = db.Column(db.Float)
    notes = db.Column(db.String(500))

    def __init__(self, user_id, body_weight_kg=None, body_fat_percent=None, waist_cm=None,
                 chest_cm=None, arm_cm=None, thigh_cm=None, notes=None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.body_weight_kg = body_weight_kg
        self.body_fat_percent = body_fat_percent
        self.waist_cm = waist_cm
        self.chest_cm = chest_cm
        self.arm_cm = arm_cm
        self.thigh_cm = thigh_cm
        self.notes = notes


class Lift(db.Model):
    """Tracks a user's personal best for a given exercise."""
    __tablename__ = "lifts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    movement_category = db.Column(db.String(50))       # squat / bench / deadlift / accessory
    variation_name = db.Column(db.String(100))          # comp, paused, touch-and-go, etc.
    best_weight_kg = db.Column(db.Float)
    best_reps = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, user_id, exercise_name, best_weight_kg=None, best_reps=None,
                 movement_category=None, variation_name=None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.exercise_name = exercise_name
        self.movement_category = movement_category
        self.variation_name = variation_name
        self.best_weight_kg = best_weight_kg
        self.best_reps = best_reps


class Workout(db.Model):
    """One training session; contains many sets."""
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    performed_at = db.Column(db.DateTime, server_default=db.func.now())
    total_volume_kg = db.Column(db.Float, default=0.0)  # sum of weight * reps across all sets

    sets = db.relationship("WorkoutSet", backref="workout", lazy=True)


class WorkoutSet(db.Model):
    """A single set within a workout."""
    __tablename__ = "workout_sets"

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey("workouts.id"), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    movement_category = db.Column(db.String(50))        # squat / bench / deadlift / accessory
    variation_name = db.Column(db.String(100))
    set_type = db.Column(db.String(50), default="working")  # top / backoff / volume / accessory
    reps = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    rpe = db.Column(db.Float)                           # Rate of Perceived Exertion (1–10)
    rir = db.Column(db.Integer)                         # Reps in Reserve
    performed_at = db.Column(db.DateTime)

    def __init__(self, workout_id, exercise_name, reps, weight_kg, movement_category=None,
                 variation_name=None, set_type="working", rpe=None, rir=None, **kwargs):
        super().__init__(**kwargs)
        self.workout_id = workout_id
        self.exercise_name = exercise_name
        self.movement_category = movement_category
        self.variation_name = variation_name
        self.set_type = set_type
        self.reps = reps
        self.weight_kg = weight_kg
        self.rpe = rpe
        self.rir = rir
