from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, dotenv_values
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
URI = f"mongodb+srv://{USERNAME}:{PASSWORD}@cluster0.f8egr.mongodb.net/?appName=Cluster0"

# TODO : func -> get collection || params -> collection_id || return -> collection data
# TODO : func -> get post || params -> post_id || return -> post data
# TODO : func -> get user collections || params -> user_id || return -> all collections of this user
# TODO : func -> get user posts || params -> user_id || return -> all posts of this user
# TODO : func -> get user saved posts || params -> user_id || return -> all saved posts of this user"
# TODO : func -> get user liked posts || params -> user_id || return -> all liked posts of this user
# TODO : func -> get user saved posts in collection || params -> user_id, collection_id || return -> all saved posts of this user in this collection
# TODO : func -> get date of post || params -> post_id || return -> date of post [NOTE: this is not in the schema, but mongodb will add it automatically]
#                 [so we can just get it from the post data and return it in a readable format - > December 12, 2023] ]

USER_SCHEMA ={
    "username": str,  # Username of the user
    "user_id": str,  # Email address of the user
    "user_pic": str,  # URL of the user's profile picture
    "location": list, # location of the user
    "location_geometry": list, # location of the user [longitude, latitude]
    "created_pins": list,  # List of post IDs created by the user
    "liked_posts": list,  # List of post IDs liked by the user
    "saved_posts": list,  # List of post IDs saved by the user
    "collections": list   # List of collection IDs created by the user
}

PIN_SCHEMA ={
    "user_id": str,  # Username of the user who created the post
    "post_id": str,  # Unique ID of the post
    "location": list, # location of the user
    "location_geometry": list, # location of the user [longitude, latitude]
    "saved_by": list,  # List of user IDs who saved the post
    "likes": list,  # List of user IDs who liked the post
    "saved_in": list,  # List of collection IDs where the post is saved
    "tags": list,  # List of tags associated with the post
    "caption": str,  # Caption of the post
    "images": list,  # List of media URLs associated with the post    
}

COLLECTION_SCHEMA ={
    "user_id": str,  # Username of the user who created the collection
    "collection_id": str,  # Unique ID of the collection
    "collection_name": str,  # Name of the collection
    "pin_ids": list  # List of post IDs saved in the collection
}




class Backend:
    def __init__(self):
        self.client = MongoClient(URI, server_api=ServerApi('1'))
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print("Failed to connect to MongoDB:", e)

        self.db = self.client["DropSpot"]
        self.pins = self.db["Pin"]
        self.users = self.db["User"]
        self.collections = self.db["Collection"]

    # Add a user
    def add_user(self, user_data):
        return self.users.insert_one(user_data)
    
    # Get a user
    def get_user(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        if user:
            # Remove the _id field from the user data
            logging.info(f"User with ID {user_id} found: {user}")
            del user["_id"]
            return user
        logging.info(f"User with ID {user_id} not found.")
        return None

    # Add a collection
    def add_collection(self, collection_data):
        return self.collections.insert_one(collection_data)

    # Add a post (pin)
    def add_post(self, post_data):
        user_id = post_data["user_id"]
        post_id = post_data["post_id"]
        self.pins.insert_one(post_data)
        self.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"created_pins": post_id}}
        )

    # Like a post
    def like_post(self, user_id, post_id):
        self.pins.update_one(
            {"post_id": post_id},
            {"$addToSet": {"likes": user_id}}
        )
        self.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"liked_posts": post_id}}
        )

    # Dislike a post
    def dislike_post(self, user_id, post_id):
        self.pins.update_one(
            {"post_id": post_id},
            {"$pull": {"likes": user_id}}
        )
        self.users.update_one(
            {"user_id": user_id},
            {"$pull": {"liked_posts": post_id}}
        )

    # Save a post
    def save_post(self, user_id, post_id, collection_ids=None):
        self.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"saved_posts": post_id}}
        )
        self.pins.update_one(
            {"post_id": post_id},
            {"$addToSet": {"saved_by": user_id}}
        )
        if collection_ids:
            for cid in collection_ids:
                self.collections.update_one(
                    {"collection_id": cid},
                    {"$addToSet": {"post_ids": post_id}}
                )

    # Unsave a post (from all collections by this user)
    def unsave_post(self, user_id, post_id):
        self.users.update_one(
            {"user_id": user_id},
            {"$pull": {"saved_posts": post_id}}
        )
        self.pins.update_one(
            {"post_id": post_id},
            {"$pull": {"saved_by": user_id}}
        )
        self.collections.update_many(
            {"user_id": user_id},
            {"$pull": {"post_ids": post_id}}
        )

    # Get tags from a post
    def get_post_tags(self, post_id):
        post = self.pins.find_one({"post_id": post_id})
        return post.get("tags", []) if post else []

    # Delete a post
    def delete_post(self, user_id, post_id):
        self.pins.delete_one({"post_id": post_id})
        self.users.update_one(
            {"user_id": user_id},
            {"$pull": {"created_pins": post_id, "saved_posts": post_id}}
        )
        self.collections.update_many(
            {},
            {"$pull": {"post_ids": post_id}}
        )

    # Delete a collection
    def delete_collection(self, user_id, collection_id):
        self.collections.delete_one({"collection_id": collection_id})
        self.users.update_one(
            {"user_id": user_id},
            {"$pull": {"collections": collection_id}}
        )
if __name__ == "__main__":
    backend = Backend()

