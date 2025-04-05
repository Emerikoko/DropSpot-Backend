from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
URI = f"mongodb+srv://{USERNAME}:{PASSWORD}@cluster0.f8egr.mongodb.net/?appName=Cluster0"

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

