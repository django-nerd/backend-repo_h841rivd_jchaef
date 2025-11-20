import os
import datetime
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGO_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "blessedbuy")

_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)
db: AsyncIOMotorDatabase = _client[DB_NAME]

async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.datetime.utcnow().isoformat()
    data = {**data, "created_at": now, "updated_at": now}
    doc = await db[collection_name].insert_one(data)
    return {"_id": str(doc.inserted_id), **data}

async def get_documents(collection_name: str, filter_dict: Dict[str, Any] | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
    cursor = db[collection_name].find(filter_dict or {})
    if limit:
        cursor = cursor.limit(limit)
    items = []
    async for item in cursor:
        item["_id"] = str(item.get("_id"))
        items.append(item)
    return items

async def update_document(collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
    update_dict["updated_at"] = datetime.datetime.utcnow().isoformat()
    res = await db[collection_name].update_one(filter_dict, {"$set": update_dict})
    return res.modified_count

async def delete_document(collection_name: str, filter_dict: Dict[str, Any]) -> int:
    res = await db[collection_name].delete_one(filter_dict)
    return res.deleted_count
