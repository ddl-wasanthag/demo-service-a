"""
Service A — entry point of the demo chain.

Call flow:  User → A → B → C → B (B handles the return leg)

GET /          status check
GET /hello     calls Service B, returns the full nested chain response
"""

import os
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Header
from typing import Annotated, Optional

app = FastAPI(title="Service A")

SERVICE_TOKEN = os.environ["SERVICE_TOKEN"]   # shared secret for app-level auth
SERVICE_B_URL = os.environ["SERVICE_B_URL"]   # vanity URL of Service B
VERIFY_SSL    = os.environ.get("VERIFY_SSL", "true").lower() != "false"


def verify_token(x_service_token: Annotated[Optional[str], Header()] = None):
    """Validate the shared service token on incoming requests."""
    if x_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Service-Token")


def call_service(url: str, path: str) -> dict:
    """
    Make an authenticated GET request to another Domino App.

    X-Domino-Api-Key authenticates against the Domino reverse proxy.
    X-Service-Token is the app-level shared secret validated by the receiving service.
    We do NOT use Authorization: Bearer here — Domino 6.1's proxy returns 500 when
    it receives a Bearer token that is not a valid JWT.
    """
    headers = {
        "X-Domino-Api-Key": SERVICE_TOKEN,
        "X-Service-Token": SERVICE_TOKEN,
    }
    response = requests.get(f"{url}{path}", headers=headers, timeout=10, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json()


@app.get("/")
def root():
    return {"service": "A", "status": "ok"}


@app.get("/hello")
def hello(x_service_token: Annotated[Optional[str], Header()] = None):
    verify_token(x_service_token)
    try:
        b_response = call_service(SERVICE_B_URL, "/hello")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not reach Service B: {e}")

    return {
        "from": "A",
        "message": "Hello from A",
        "downstream": b_response,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8888)))
