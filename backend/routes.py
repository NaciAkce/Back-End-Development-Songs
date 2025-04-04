from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

######################################################################
# RETURN HEALTH OF THE APP
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200

######################################################################
# COUNT THE NUMBER OF SONGS
######################################################################
@app.route("/count", methods=["GET"])
def count():
    """Return the number of songs in the database"""
    count = db.songs.count_documents({})
    return jsonify({"count": count}), 200

######################################################################
# GET ALL SONGS
######################################################################
@app.route("/song", methods=["GET"])
def songs():
    """Get all songs from the database"""
    all_songs = list(db.songs.find({}))
    return jsonify({"songs": parse_json(all_songs)}), 200

######################################################################
# GET A SONG BY ID
######################################################################
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """Get a song by its id"""
    song = db.songs.find_one({"id": id})
    if song:
        return jsonify(parse_json(song)), 200
    else:
        return jsonify({"message": "song with id not found"}), 404

######################################################################
# CREATE A NEW SONG
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    """Create a new song in the database"""
    song = request.json
    
    # Check if a song with the same ID already exists
    existing_song = db.songs.find_one({"id": song["id"]})
    if existing_song:
        return jsonify({"Message": f"song with id {song['id']} already present"}), 302
    
    # Insert the new song into the database
    result = db.songs.insert_one(song)
    
    # Return the ID of the newly created song
    return jsonify({"inserted id": parse_json(result.inserted_id)}), 201

######################################################################
# UPDATE A SONG
######################################################################
@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    """Update a song in the database"""
    # Extract the updated data from the request
    song_data = request.json
    
    # Find the song in the database
    existing_song = db.songs.find_one({"id": id})
    
    # If the song does not exist, return 404
    if not existing_song:
        return jsonify({"message": "song not found"}), 404
    
    # Update the song with the new data
    result = db.songs.update_one(
        {"id": id},
        {"$set": song_data}
    )
    
    # Check if any documents were modified
    if result.modified_count == 0:
        return jsonify({"message": "song found, but nothing updated"}), 200
    
    # Return the updated song
    updated_song = db.songs.find_one({"id": id})
    return jsonify(parse_json(updated_song)), 201

######################################################################
# DELETE A SONG
######################################################################
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    """Delete a song from the database"""
    # Delete the song from the database
    result = db.songs.delete_one({"id": id})
    
    # Check if any documents were deleted
    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    
    # Return no content for a successful delete
    return "", 204