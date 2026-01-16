from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase

async def next_server_seq(db: AsyncIOMotorDatabase, conv_id: str) -> int:
    res = await db["counters"].find_one_and_update(
        {"_id": conv_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True  
    )
    if not res:
        res = await db["counters"].find_one({"_id": conv_id})
    return int(res.get("seq", 1))

async def next_conv_seq(db: AsyncIOMotorDatabase, user_id: str) -> int:
    res = await db["counters"].find_one_and_update(
        {"_id": f"conv:{user_id}"},   
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    if not res:
        res = await db["counters"].find_one({"_id": f"conv:{user_id}"})
    return int(res.get("seq", 1))
