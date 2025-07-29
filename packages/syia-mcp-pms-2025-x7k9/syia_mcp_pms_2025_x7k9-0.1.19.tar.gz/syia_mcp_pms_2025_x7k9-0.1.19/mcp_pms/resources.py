from mcp_pms import *
import mcp.types as types
from typing import Union
from pydantic import AnyUrl
from pymongo import MongoClient
from mcp_pms.databases import MongoDBClient
from bson.objectid import ObjectId
from urllib.parse import urlparse
import json

client = MongoClient("mongodb://syia-etl-dev:SVWvsnr6wAqKG1l@db-etl.prod.syia.ai:27017/?authSource=syia-etl-dev")
db = client["syia-etl-dev"]


resource_list = [
    types.Resource(
        uri="imo://overview/<imo>",
        name="Overview of PMS Weekly review of Fleet vessels",
        description="Overview of PMS Weekly review of Fleet vessels",
        mimeType="application/json",
    ),
    types.Resource(
        uri="imo://pms_summary/<imo>",
        name="PMS Summary",
        description="PMS Summary",
        mimeType="application/json",
    ),
    types.Resource(
        uri="imo://status/<imo>",
        name="PMS Status",
        description="PMS Status",
        mimeType="application/json",
    ),
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

        if parsed.scheme == "imo":
            if resource_type == "overview":
                return json.dumps(get_overview(identifier), indent=2)
            elif resource_type == "pms_summary":
                return json.dumps(get_summary(identifier), indent=2)
            elif resource_type == "status":
                return json.dumps(get_status(identifier), indent=2)
        elif parsed.scheme == "user" and resource_type == "details":
            return json.dumps(await get_user_details(identifier), indent=2)
        else:
            return f"Resource not found for uri: {uri_str}"


def get_overview(imo: str) -> dict:
    try:
        collection = db["vesselinfos"]
        query = {"imo": int(imo), 
                 "questionNo": 114}
        projection = {"_id": 0, "answer": 1, "vesselName": 1}
        result = collection.find_one(query, projection)
        return result
    except Exception as e:
        return {"error": str(e)}

def get_summary(imo: str) -> dict:
    try:
        collection = db["vesselinfos"]
        query = {"imo": int(imo), 
                 "questionNo": 116}
        projection = {"_id": 0,  "answer": 1, "vesselName": 1}
        result = collection.find_one(query, projection)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_status(imo: str) -> dict:
    try:
        collection = db["vesselinfos"]
        query = {"imo": int(imo), 
                 "questionNo": 136}
        projection = {"_id": 0, "answer": 1, "vesselName": 1}
        result = collection.find_one(query, projection)
        return result
    except Exception as e:
        return {"error": str(e)}

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










