from mcp_voyage import *
import mcp.types as types
from typing import Union
from pydantic import AnyUrl
from mcp_voyage.databases import MongoDBClient
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
        resource_type = parsed.netloc  # e.g., 'pms_summary'
        identifier = parsed.path.lstrip('/')  # e.g., '1234567' or user_id

        if parsed.scheme == "user" and resource_type == "details":
            return json.dumps(await get_user_details(identifier), indent=2)
        else:
            return f"Resource not found for uri: {uri_str}"

       

async def get_user_details(user_id: str) -> dict:
    try:
        mongo_client = MongoDBClient()
        dev_db = mongo_client.db
        collection = dev_db["users"]
        query = {"_id": ObjectId(user_id)}
        projection = {"_id": 0, "firstName": 1, "lastName": 1, "email": 1, "phone": 1}
        result = await collection.find_one(query, projection)
        return result
    except Exception as e:
        return {"error": str(e)}










