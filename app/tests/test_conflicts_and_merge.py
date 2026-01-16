import pytest

BASE_URL = "/messages"

@pytest.mark.anyio
async def test_conflict_409(client):    
    init = {"_id": "mc1", "conv_id": "cX", "user_id": "uX", "role": "user", "content": "v1"}
    await client.post(BASE_URL, json=init)
    
    base = (await client.get(f"{BASE_URL}?selector={{\"_id\":\"mc1\"}}")).json()[0]
    
    await client.post(BASE_URL, json={"_id": "mc1", "conv_id": "cX", "user_id": "uX", "role": "user", "content": "v2"})
    
    patch_payload = {
        "doc":  {"_id": "mc1", "conv_id": "cX", "user_id": "uX", "role": "user", "content": "v3"},
        "base": base
    }
    r = await client.patch(BASE_URL, json=patch_payload)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "serverDoc" in detail
    assert detail["serverDoc"]["content"] == "v2"
