from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv, dotenv_values
import logging
from bson.objectid import ObjectId
from datetime import datetime

logging.basicConfig(level=logging.INFO)
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

    # Get collection
    def get_collection(self, collection_id):
        collection =  self.collections.find_one({"collection_id" : collection_id})
        if collection:
            logging.info(f"Collection with ID {collection_id} found: {collection}")
            del collection["_id"]
            return collection
        logging.info(f"Collection with ID {collection_id} not found: {collection}")
        return None
    
    # Get post
    def get_post(self, post_id):
        post =  self.pins.find_one({"post_id" : post_id})
        if post:
            logging.info(f"Post with ID {post_id} found: {post}")
            del post["_id"]
            return post
        logging.info(f"Post with ID {post_id} found: {post}")
        return None
    
    import logging

    # Get user collections
    def get_user_collections(self, user_id):
        collections = list(self.collections.find({"user_id": user_id}))
        for collection in collections:
            del collection["_id"]
        logging.info(f"Found {len(collections)} collections for user {user_id}.")
        return collections

    # Get all user's posts
    def get_user_posts(self, user_id):
        posts = list(self.pins.find({"user_id": user_id}))
        for post in posts:
            del post["_id"]
        logging.info(f"Found {len(posts)} posts for user {user_id}.")
        return posts

    # Get all posts saved by a user
    def get_saved_posts_by_user(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        if not user or "saved_posts" not in user:
            logging.info(f"No saved posts found for user {user_id}.")
            return []
        posts = list(self.pins.find({"post_id": {"$in": user["saved_posts"]}}))
        for post in posts:
            del post["_id"]
        logging.info(f"Found {len(posts)} saved posts for user {user_id}.")
        return posts

    # Get all posts liked by a user
    def get_liked_posts_by_user(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        if not user or "liked_posts" not in user:
            logging.info(f"No liked posts found for user {user_id}.")
            return []
        posts = list(self.pins.find({"post_id": {"$in": user["liked_posts"]}}))
        for post in posts:
            del post["_id"]
        logging.info(f"Found {len(posts)} liked posts for user {user_id}.")
        return posts

    # Get all posts saved by a user in a specific collection
    def get_saved_posts_in_collection(self, user_id, collection_id):
        collection = self.collections.find_one({
            "collection_id": collection_id,
            "user_id": user_id
        })
        if not collection or "post_ids" not in collection:
            logging.info(f"No posts found in collection {collection_id} for user {user_id}.")
            return []
        post_ids = collection["post_ids"]
        posts = list(self.pins.find({"post_id": {"$in": post_ids}}))
        for post in posts:
            del post["_id"]
        logging.info(f"Found {len(posts)} posts in collection {collection_id} for user {user_id}.")
        return posts

    # Get date of post based on MongoDB _id timestamp
    def get_post_date(self, post_id):
        post = self.pins.find_one({"post_id": post_id})
        if not post:
            logging.info(f"Post with ID {post_id} not found.")
            return None
        timestamp = post["_id"].generation_time
        formatted_date = timestamp.strftime("%B %d, %Y")
        logging.info(f"Post {post_id} was created on {formatted_date}.")
        return formatted_date


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

