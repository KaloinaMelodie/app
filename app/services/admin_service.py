from motor.motor_asyncio import AsyncIOMotorDatabase
import os

_BOOT = {e.strip().lower() for e in os.getenv("ADMINS_BOOTSTRAP_EMAILS", "").split(",") if e.strip()}

def is_bootstrap_admin(email: str | None) -> bool:
    return (email or "").strip().lower() in _BOOT

async def is_admin_in_db(db: AsyncIOMotorDatabase, email: str | None, username: str | None) -> bool:
    email_l = (email or "").strip().lower()
    user_l = (username or "").strip().lower()
    if not email_l and not user_l:
        return False
    q = {"$or": []}
    if email_l:
        q["$or"].append({"email": email_l})
    if user_l:
        q["$or"].append({"username": user_l})
    if not q["$or"]:
        return False
    doc = await db["admins"].find_one(q)
    return bool(doc)
