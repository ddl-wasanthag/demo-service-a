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

# Domino Secure App Identity endpoint — available inside every Domino app pod when
# SecureIdentityPropagationToAppsEnabled is ON.  Returns a short-lived JWT that the
# Domino proxy accepts as Bearer auth for calls to other apps (deep-linking mode).
_IDENTITY_TOKEN_URL = "http://localhost:8899/access-token"


def get_proxy_headers() -> dict:
    """
    Return the headers needed to authenticate outbound calls through the Domino proxy.

    Two modes (detected at runtime):
      1. SecureIdentityPropagation ON  → fetch JWT from localhost:8899 and send as Bearer.
         The proxy validates the JWT and forwards the request.
      2. SecureIdentityPropagation OFF → fall back to X-Domino-Api-Key (works with Domino
         6.2+ deep-linking where the proxy accepts API keys for direct-proxy apps).
    """
    try:
        r = requests.get(_IDENTITY_TOKEN_URL, timeout=5)
        r.raise_for_status()
        token = r.text.strip()
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        pass
    # Fallback: API-key auth (Domino 6.2+ without SecureIdentityPropagation)
    return {"X-Domino-Api-Key": SERVICE_TOKEN}


def verify_token(x_service_token: Annotated[Optional[str], Header()] = None):
    if x_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Service-Token")


def call_service(url: str, path: str) -> dict:
    headers = {
        **get_proxy_headers(),
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
