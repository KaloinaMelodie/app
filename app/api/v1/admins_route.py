from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.admins import AdminCreate, AdminUpdate, AdminOut
from app.base.db import get_db
from app.exceptions.exceptions import BadRequestException, NotFoundException, ValueControlException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.v1.auth_route import require_admin  
import logging
from bson import ObjectId

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admins")

def _to_out(doc) -> AdminOut:
    return AdminOut(
        id=str(doc["_id"]),
        email=doc.get("email"),
        username=doc.get("username"),
        created_at_server=doc["created_at_server"],
        updated_at_server=doc["updated_at_server"],
    )


@router.get("", response_model=List[AdminOut])
async def list_admins(
    q: Optional[str] = Query(default=None, description="filtre contains"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):    
    try:
        filt = {}
        if q:
            ql = q.strip().lower()
            filt = {"$or": [{"email": {"$regex": ql}}, {"username": {"$regex": ql}}]}
        cur = db["admins"].find(filt).sort("email", 1)
        return [_to_out(doc) async for doc in cur]
    except HTTPException as he:
        import traceback
        traceback_str = traceback.format_exc()
        raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))

@router.post("", status_code=201)
async def create_admin(
    payload: AdminCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        now = datetime.utcnow()
        doc = {
            "created_at_server": now,
            "updated_at_server": now,
        }
        if payload.email:
            doc["email"] = payload.email.strip().lower()
        if payload.username:
            doc["username"] = payload.username.strip().lower()

        logger.info(doc)
        res = await db["admins"].insert_one(doc)
        doc["_id"] = res.inserted_id
        return _to_out(doc)
    except HTTPException as he:        
        raise he
    except Exception as e:
        msg = str(e)
        import traceback
        traceback_str = traceback.format_exc()
        logger.warning(traceback_str)
        if "E11000" in msg:
            raise ValueControlException("email ou username déjà existant")
        raise

@router.get("/{admin_id}", response_model=AdminOut)
async def get_admin(admin_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        doc = await db["admins"].find_one({"_id":  ObjectId(admin_id)})
        if not doc:
            raise NotFoundException("admin introuvable")
        return _to_out(doc)
    except HTTPException as he:
            raise he
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        raise Exception(str(e))

@router.patch("/{admin_id}", response_model=AdminOut)
async def update_admin(admin_id: str, payload: AdminUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):    

    updates = {}
    if payload.email is not None:
        updates["email"] = payload.email.strip().lower()
    if payload.username is not None:
        updates["username"] = payload.username.strip().lower()
    if not updates:
        raise BadRequestException("Pas de champ à mettre à jour")

    updates["updated_at_server"] = datetime.utcnow()

    try:
        res = await db["admins"].find_one_and_update(
            {"_id": ObjectId(admin_id)},
            {"$set": updates},
            return_document=True  
        )
    except Exception as e:
        msg = str(e)
        if "E11000" in msg:
            raise ValueControlException("email ou username déjà existant")
        raise

    if not res:
        raise NotFoundException("admin introuvable")
    return _to_out(res)

@router.delete("/{admin_id}", status_code=204)
async def delete_admin(admin_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):  
    res = await db["admins"].delete_one({"_id": ObjectId(admin_id)})
    if res.deleted_count == 0:
        raise NotFoundException("admin introuvable")
    return
