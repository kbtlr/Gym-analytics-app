from flask_login import UserMixin
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Step-2 registration fields (all nullable until filled in)
    experience_level = db.Column(db.String(50))   # e.g. beginner / intermediate / advanced
    program_length_weeks = db.Column(db.Integer)
    target_weekly_sets = db.Column(db.Integer)     # aspiring volume

    # Relationships
    lifts = db.relationship("Lift", backref="user", lazy=True)
    workouts = db.relationship("Workout", backref="user", lazy=True)


class Lift(db.Model):
    """Tracks a user's personal best for a given exercise."""
    __tablename__ = "lifts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    best_weight_kg = db.Column(db.Float)
    best_reps = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, server_default=db.func.now())


class Workout(db.Model):
    """One training session; contains many sets."""
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    performed_at = db.Column(db.DateTime, server_default=db.func.now())
    total_volume_kg = db.Column(db.Float, default=0.0)   # sum of sets * weight

    sets = db.relationship("WorkoutSet", backref="workout", lazy=True)


class WorkoutSet(db.Model):
    """A single set within a workout."""
    __tablename__ = "workout_sets"

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey("workouts.id"), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
