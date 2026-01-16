from __future__ import annotations
import logging
from typing import Any, Dict, List, Tuple
from fastapi import APIRouter, HTTPException, Path, Query, Body
from datetime import datetime, timezone
from uuid import uuid4
from fastapi.encoders import jsonable_encoder

from app.utils.utils import md5_hex
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.base.db import get_db
from app.utils.json_params import parse_selector, parse_fields, parse_sort, parse_limit
from app.utils.merge import three_way_merge
from app.utils.seq import next_server_seq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_COLLECTIONS = {"conversations", "messages","admins"}
SERVER_ONLY = {"rev", "created_at_server", "updated_at_server", "server_seq"}

def _sanitize_for_set(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k not in SERVER_ONLY and k != "_id"}

def _strip_server_fields(d: dict | None) -> dict:
    if not isinstance(d, dict): 
        return {}
    return {k: v for k, v in d.items() if k not in SERVER_ONLY}


def _coll(db: AsyncIOMotorDatabase, name: str):
    if name not in ALLOWED_COLLECTIONS:
        logger.info(f"Collection not allowed: {name}")
        raise HTTPException(404, detail="Collection not found")
    return db[name]

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _ensure_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" not in doc or not doc["_id"]:
        doc["_id"] = str(uuid4())
    return doc

def _ensure_server_fields_for_insert(doc: Dict[str, Any]) -> None:
    now = _now()
    doc.setdefault("created_at_server", now)
    doc["updated_at_server"] = now
    doc.setdefault("deleted", False)

@router.post("/collection/{collection}")
async def upsert_docs(
    collection: str = Path(...),
    payload: Dict[str, Any] | List[Dict[str, Any]] = Body(...),
):
    db = get_db()
    coll = _coll(db, collection)

    docs = payload if isinstance(payload, list) else [payload]
    out: List[Dict[str, Any]] = []
    for d in docs:
        _ensure_id(d)
        coll = _coll(db, collection)

        # Règles de base & validations
        if collection == "messages" and not d.get("conv_id"):
            raise HTTPException(400, detail="messages require 'conv_id'")

        # Existe déjà ?
        existing = await coll.find_one({"_id": d["_id"]})

        now = _now()

        # $set: NE JAMAIS inclure created_at_server, rev, server_seq
        to_set = _sanitize_for_set(d)
        to_set["updated_at_server"] = now
        to_set.setdefault("deleted", False)

        # $setOnInsert: créé uniquement à l'insert
        set_on_insert = {"created_at_server": now}

        # server_seq: attribuer uniquement à la création d'un message
        if existing is None and collection == "messages":
            seq = await next_server_seq(get_db(), d["conv_id"])
            set_on_insert["server_seq"] = seq
        
        if existing is None and collection == "conversations":
            user_id = d.get("user_id")
            if not user_id:
                raise HTTPException(400, detail="conversations require 'user_id'")
            seq = await next_server_seq(get_db(), f"conv:{user_id}")
            set_on_insert["server_seq"] = seq

        final = await coll.find_one_and_update(
            {"_id": d["_id"]},
            {
                "$setOnInsert": set_on_insert,  
                "$set": to_set,                
                "$inc": {"rev": 1},            
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        out.append(final)


    return out if isinstance(payload, list) else out[0]


@router.patch("/collection/{collection}")
async def patch_docs(
    collection: str = Path(...),
    payload: Dict[str, Any] = Body(...),
):
   

    db = get_db()
    coll = _coll(db, collection)

    doc = payload.get("doc") 
    base = payload.get("base")
    if doc is None:
        raise HTTPException(400, detail="Missing 'doc' in payload")

    docs = doc if isinstance(doc, list) else [doc]
    bases = base if isinstance(base, list) else [base] * len(docs)
    if len(bases) != len(docs):
        raise HTTPException(400, detail="'doc' and 'base' length mismatch")

    now = _now()
    results: List[Dict[str, Any]] = []

    for d, b in zip(docs, bases):
        if not isinstance(d, dict) or "_id" not in d:
            raise HTTPException(400, detail="Each 'doc' must include an '_id'")
        _id = d["_id"]

        # On ne fait JAMAIS confiance au client pour ces champs
        d = dict(d)
        d.pop("rev", None)
        d.pop("created_at_server", None)
        d.pop("updated_at_server", None)

        current = await coll.find_one({"_id": _id})

        # Si le doc n'existe pas encore -> insertion
        if current is None:
            if collection == "messages" and not d.get("conv_id"):
                raise HTTPException(400, detail="messages require 'conv_id'")
            
            if collection == "conversations":
                user_id = d.get("user_id")
                if not user_id:
                    raise HTTPException(400, detail="conversations require 'user_id'")
                seq = await next_server_seq(get_db(), f"conv:{user_id}")
                set_on_insert["server_seq"] = seq

            now = _now()
            to_set = _sanitize_for_set(d)
            to_set["updated_at_server"] = now
            to_set.setdefault("deleted", False)

            set_on_insert = {"created_at_server": now}
            if collection == "messages":
                seq = await next_server_seq(get_db(), d["conv_id"])
                set_on_insert["server_seq"] = seq

            final = await coll.find_one_and_update(
                {"_id": _id},
                {
                    "$setOnInsert": set_on_insert,
                    "$set": to_set,
                    "$inc": {"rev": 1},
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            results.append(final)
            continue


        # Merge 3-voies si 'base' fourni, sinon LWW
        if isinstance(b, dict):
            base_for_merge    = _strip_server_fields(b)
            doc_for_merge     = _strip_server_fields(d)
            current_for_merge = _strip_server_fields(current)
            # merged, conflicted = three_way_merge(b, d, current)
            merged, conflicted = three_way_merge(base_for_merge, doc_for_merge, current_for_merge)

            if conflicted:
                server_doc_safe = jsonable_encoder(current)  # datetimes -> str ISO 8601
                raise HTTPException(
                    status_code=409,
                    detail={"message": "Conflit lors du 3-way merge", "serverDoc": server_doc_safe},
                )
            to_write = merged
        else:
            to_write = dict(d)

        to_write["_id"] = _id
        if collection == "messages" and "server_seq" in current:
            to_write["server_seq"] = current["server_seq"]
        if collection == "conversations" and "server_seq" in current:
            to_write["server_seq"] = current["server_seq"]
        to_write["deleted"] = to_write.get("deleted", current.get("deleted", False))
        now = _now()
        to_set = _sanitize_for_set(to_write)  
        to_set["updated_at_server"] = now     

        final = await coll.find_one_and_update(
            {"_id": _id},
            { 
                "$set": to_set,
                "$inc": {"rev": 1},  
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        results.append(final)

    return results if isinstance(doc, list) else results[0]

@router.get("/collection/{collection}")
async def find_docs(
    collection: str = Path(...),
    selector: str | None = Query(default=None),
    fields: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    limit: int | None = Query(default=None),
):
    db = get_db()
    coll = _coll(db, collection)

    sel = parse_selector(selector)
    proj = parse_fields(fields)
    srt = parse_sort(sort)
    if not srt :#and collection == "conversations":
        srt = [("server_seq", 1)]
    lim = parse_limit(str(limit) if limit is not None else None, default=100)

    if "deleted" not in sel:
        sel["deleted"] = {"$ne": True}

    cursor = coll.find(sel, proj)
    if srt:
        cursor = cursor.sort(srt)
    cursor = cursor.limit(lim)

    docs = await cursor.to_list(length=lim)
    return docs

@router.delete("/collection/{collection}/{doc_id}")
async def delete_doc(
    collection: str = Path(...),
    doc_id: str = Path(...),
):
    db = get_db()
    coll = _coll(db, collection)

    now = _now()
    res = await coll.update_one(
        {"_id": doc_id},
        {"$set": {"deleted": True, "updated_at_server": now}, "$inc": {"rev": 1}},
        upsert=False,
    )
    final = await coll.find_one({"_id": doc_id})
    if final is None:
        raise HTTPException(status_code=410, detail="Document not found for deletion")
    return {"status": "ok", "_id": doc_id, "deleted": True}

 # 1000 messages par shard par conversation
SHARD_SIZE = 1000 

def bucket_of(server_seq: int) -> int:
    return server_seq // SHARD_SIZE

@router.post("/collection/messages/quickfind")
async def quickfind_messages(
    payload: Dict[str, Any] = Body(...),
):
    db: AsyncIOMotorDatabase = get_db()
    conv_id = payload.get("conv_id")
    if not conv_id:
        raise HTTPException(400, detail="conv_id is required")

    client_shards = payload.get("client", [])
    if not isinstance(client_shards, list):
        raise HTTPException(400, detail="client must be a list of shard summaries")

    fields = payload.get("fields")
    projection = None
    if isinstance(fields, list) and fields:
        projection = {k: 1 for k in fields}
    else:
        projection = {
            "_id": 1, "conv_id": 1, "user_id": 1, "role": 1, "content": 1,
            "deleted": 1, "server_seq": 1, "updated_at_server": 1, "rev": 1
        }

    limit_docs = int(payload.get("limit_docs", 5000))

    client_map: Dict[int, Dict[str, Any]] = {}
    for s in client_shards:
        b = int(s.get("bucket", -1))
        if b >= 0:
            client_map[b] = {"count": int(s.get("count", 0)), "hash": str(s.get("hash", ""))}

    cursor = db["messages"].find(
        {"conv_id": conv_id},
        {"_id": 1, "rev": 1, "deleted": 1, "server_seq": 1}
    ).sort([("server_seq", 1)])

    server_buckets: Dict[int, List[Dict[str, Any]]] = {}
    total = 0
    async for doc in cursor:
        total += 1
        seq = int(doc.get("server_seq", 0))
        b = bucket_of(seq)
        server_buckets.setdefault(b, []).append(doc)

    changed_buckets: List[int] = []
    server_summaries: Dict[int, Dict[str, Any]] = {}

    for b, docs in server_buckets.items():
        count = len(docs)
        h = md5_hex(f"{d['_id']}:{d.get('rev',0)}:{1 if d.get('deleted') else 0};" for d in docs)
        server_summaries[b] = {"count": count, "hash": h}
        cli = client_map.get(b)
        if not cli or cli["count"] != count or cli["hash"] != h:
            changed_buckets.append(b)

   
    for b in client_map.keys():
        if b not in server_summaries:
            changed_buckets.append(b)

    changed_buckets = sorted(set(changed_buckets))

    if not changed_buckets:
        return {
            "conv_id": conv_id,
            "changed_buckets": [],
            "summaries": {str(k): v for k, v in server_summaries.items()},
            "docs": []
        }

    docs_out: List[Dict[str, Any]] = []
    fetched = 0
    for b in changed_buckets:
        q = {
            "conv_id": conv_id,
            "server_seq": {"$gte": b * SHARD_SIZE, "$lt": (b + 1) * SHARD_SIZE}
        }
        cursor2 = db["messages"].find(q, projection).sort([("server_seq", 1)])
        async for d in cursor2:
            docs_out.append(d)
            fetched += 1
            if fetched >= limit_docs:
                break
        if fetched >= limit_docs:
            break

    return {
        "conv_id": conv_id,
        "changed_buckets": changed_buckets,
        "summaries": {str(k): v for k, v in server_summaries.items()},
        "docs": docs_out
    }

@router.post("/collection/conversations/quickfind")
async def quickfind_conversations(payload: Dict[str, Any] = Body(...)):
    db: AsyncIOMotorDatabase = get_db()
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(400, detail="user_id is required")

    client_buckets = payload.get("client", [])
    if not isinstance(client_buckets, list):
        raise HTTPException(400, detail="client must be a list of shard summaries")

    limit_docs = int(payload.get("limit_docs", 1000))

    cursor = db["conversations"].find(
        {"user_id": user_id},
        {"_id": 1, "rev": 1, "deleted": 1, "server_seq": 1}
    ).sort([("server_seq", 1)])

    server_buckets: Dict[int, List[Dict[str, Any]]] = {}
    async for doc in cursor:
        seq = int(doc.get("server_seq", 0))
        b = bucket_of(seq) 
        server_buckets.setdefault(b, []).append(doc)

    server_summaries, changed_buckets = {}, []
    for b, docs in server_buckets.items():
        h = md5_hex(f"{d['_id']}:{d.get('rev',0)}:{1 if d.get('deleted') else 0};" for d in docs)
        server_summaries[b] = {"count": len(docs), "hash": h}
        cli = next((c for c in client_buckets if int(c["bucket"]) == b), None)
        if not cli or cli["count"] != len(docs) or cli["hash"] != h:
            changed_buckets.append(b)

    docs_out: List[Dict[str, Any]] = []
    for b in changed_buckets:
        q = {"user_id": user_id, "server_seq": {"$gte": b*SHARD_SIZE, "$lt": (b+1)*SHARD_SIZE}}
        async for d in db["conversations"].find(q).sort([("server_seq", 1)]):
            docs_out.append(d)
            if len(docs_out) >= limit_docs:
                break

    return {
        "user_id": user_id,
        "changed_buckets": changed_buckets,
        "summaries": server_summaries,
        "docs": docs_out,
    }
