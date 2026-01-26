from flask import Blueprint, jsonify

main = Blueprint("main", __name__)

@main.route("/api/route")
def route():
    return jsonify({"Received by /api/hello"})
