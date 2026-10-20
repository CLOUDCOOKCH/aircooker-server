from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aircooker.app import create_app


@pytest.fixture
def harness(tmp_path):
    app = create_app(tmp_path, run_worker=False)
    device = str(uuid4())
    with TestClient(app) as client:
        token = (tmp_path / "config" / "setup-token").read_text()
        response = client.post(
            "/api/v1/setup",
            headers={"X-Setup-Token": token},
            json={
                "name": "Test household",
                "timezone": "Europe/Zurich",
                "language": "en",
                "username": "cook",
                "password": "a strong test password",
                "device_id": device,
            },
        )
        assert response.status_code == 201, response.text
        tokens = response.json()
        client.headers["Authorization"] = "Bearer " + tokens["access_token"]
        yield client, app, device, tokens


@pytest.fixture
def mutation():
    def make(device, kind="recipe", entity_id=None, base=0, payload=None, operation="upsert"):
        mid = str(uuid4())
        return {
            "mutation_id": mid,
            "entity_id": entity_id or str(uuid4()),
            "kind": kind,
            "operation": operation,
            "base_revision": base,
            "payload": payload
            if payload is not None
            else {"title": "Soup", "servings": "2", "ingredients": [], "steps": ["Cook"]},
            "device_id": device,
            "client_timestamp": "2000-01-01T00:00:00Z",
            "idempotency_key": mid,
        }

    return make
