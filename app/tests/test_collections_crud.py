import pytest

BASE_URL = "/messages"

@pytest.mark.anyio
async def test_upsert_and_find(client):    
    doc = {"_id": "m1", "conv_id": "c1", "user_id": "u1", "role": "user", "content": "hello"}
    r = await client.post(BASE_URL, json=doc)
    assert r.status_code == 200
    created = r.json()
    assert created["_id"] == "m1"
    assert created["deleted"] is False
    assert "updated_at_server" in created
    assert created["rev"] >= 1
    
    r = await client.get(f"{BASE_URL}?selector={{\"conv_id\":\"c1\"}}&limit=10")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) == 1
    assert arr[0]["_id"] == "m1"

@pytest.mark.anyio
async def test_patch_lww_and_tombstone(client):    
    await client.post(BASE_URL, json={"_id": "m2", "conv_id": "c1", "user_id": "u1", "role": "user", "content": "A"})
    
    current = (await client.get(f"{BASE_URL}?selector={{\"_id\":\"m2\"}}")).json()[0]
    
    payload = {
        "doc":  {"_id": "m2", "conv_id": "c1", "user_id": "u1", "role": "user", "content": "B"},
        "base": current
    }
    r = await client.patch(BASE_URL, json=payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated["content"] == "B"
    assert updated["rev"] >= current["rev"] + 1
    
    r = await client.delete(f"{BASE_URL}/m2")
    assert r.status_code == 200
    assert r.json()["deleted"] is True
    
    r = await client.get(f"{BASE_URL}?selector={{\"conv_id\":\"c1\"}}")
    assert r.status_code == 200
    arr = r.json()
    assert all(not d.get("deleted") for d in arr)
    assert all(d["_id"] != "m2" for d in arr)
    
    r = await client.get(f"{BASE_URL}?selector={{\"_id\":\"m2\",\"deleted\":true}}")
    arr = r.json()
    assert len(arr) == 1 and arr[0]["deleted"] is True
