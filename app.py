# drop_spot_api.py

from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from drop_spot_backend import get_database, insert_pins, get_pins_by_location, insert_user, get_user_saved_pins, create_collection, get_user_collections, get_pins_in_collection

load_dotenv()
app = Flask(__name__)
db = get_database()

@app.route("/api/pins", methods=[POST])
def add_pins():
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid pin data"}), 400
    success = insert_pins(db, data)
    return jsonify({"success": success}), (200 if success else 500)

@app.route("/api/pins/location/<location>", methods=["GET"])
def search_pins_by_location(location):
    pins = get_pins_by_location(db, location)
    return jsonify(pins), 200

@app.route("/api/users", methods=["POST"])
def add_user():
    user_data = request.json
    if not user_data:
        return jsonify({"error": "Invalid user data"}), 400
    success = insert_user(db, user_data)
    return jsonify({"success": success}), (200 if success else 500)

@app.route("/api/users/<user_id>/saved_pins", methods=["GET"])
def get_saved_pins(user_id):
    pins = get_user_saved_pins(db, user_id)
    return jsonify(pins), 200

@app.route("/api/collections", methods=["POST"])
def add_collection():
    collection_data = request.json
    if not collection_data:
        return jsonify({"error": "Invalid collection data"}), 400
    success = create_collection(db, collection_data)
    return jsonify({"success": success}), (200 if success else 500)

@app.route("/api/collections/user/<user_id>", methods=["GET"])
def get_collections_by_user(user_id):
    collections = get_user_collections(db, user_id)
    return jsonify(collections), 200

@app.route("/api/collections/<collection_id>/pins", methods=["GET"])
def get_collection_pins(collection_id):
    pins = get_pins_in_collection(db, collection_id)
    return jsonify(pins), 200

if __name__ == "__main__":
    app.run(debug=True)
