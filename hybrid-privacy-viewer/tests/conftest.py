import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import hash_password
from app.config import Settings
from app.main import create_app

DATA = Path(__file__).resolve().parent.parent / "sample-data"


@pytest.fixture
def settings(tmp_path):
    accounts = tmp_path / "accounts.json"
    accounts.write_text(json.dumps({"accounts": [
        {"username": "policy01", "name": "정책", "role": "policy", "password_hash": hash_password("pw-policy", 1000)},
        {"username": "security01", "name": "보안", "role": "security", "password_hash": hash_password("pw-security", 1000)},
    ]}), encoding="utf-8")
    return Settings(git_sha="abc1234", data_dir=DATA, accounts_file=accounts, session_secret="test", max_login_failures=3)


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=False)


@pytest.fixture
def policy(client):
    assert login(client, "policy01", "pw-policy").status_code == 303
    return client


@pytest.fixture
def security(client):
    assert login(client, "security01", "pw-security").status_code == 303
    return client
