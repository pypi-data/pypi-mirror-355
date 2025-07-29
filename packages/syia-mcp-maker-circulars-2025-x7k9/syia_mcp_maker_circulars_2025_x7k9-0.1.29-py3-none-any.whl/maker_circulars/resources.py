from maker_circulars import *
import mcp.types as types
from pydantic import AnyUrl
from maker_circulars.databases import MongoDBClient
from bson.objectid import ObjectId
from urllib.parse import urlparse
import json



resource_list = [
    types.Resource(
        uri="user://details/<user_id>",
        name="User Details",
        description="Details about the user based on the given user id",
        mimeType="application/json",
    ) 
]


def register_resources():
    @mcp.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        # Return a general resource description, instructing users to provide an IMO number
        return resource_list
    @mcp.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        uri_str = str(uri)
        parsed = urlparse(uri_str)
        resource_type = parsed.netloc  # e.g., 'survey_summary'
        identifier = parsed.path.lstrip('/')  # e.g., '1234567' or user_id

        if parsed.scheme == "user" and resource_type == "details":
            user_details = await get_user_details(identifier)
            return json.dumps(user_details, indent=2)
        else:
            return f"Resource not found for uri: {uri_str}"



async def get_user_details(user_id: str) -> dict:
    try:
        mongo_client = MongoDBClient()
        dev_db = mongo_client.db
        collection = dev_db["users"]
        query = {"_id": ObjectId(user_id)}
        projection = {"_id": 0, "firstName": 1, "lastName": 1, "email": 1,"phone":1}
        result = await collection.find_one(query, projection)
        
        if result is None:
            return {"error": "User not found"}
            
        # Ensure the result is a Python dict
        return dict(result) if result else {}
    except Exception as e:
        return {"error": str(e)}










