"""Diagnostic CLI utility to inspect raw ICICI Breeze API responses.

Usage:
    docker compose exec backend python /app/scripts/inspect_icici_raw.py
    or with custom token:
    docker compose exec backend python /app/scripts/inspect_icici_raw.py --session-token <TOKEN>
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

# Ensure app is on path
sys.path.insert(0, "/app")

from app.crud.crud_broker import crud_broker
from app.db.session import SessionLocal
from app.models.broker_credential import BrokerCredential

BREEZE_BASE_URL = "https://api.icicidirect.com/breezeapi/api/v1"


def compute_signature(timestamp: str, payload_str: str, secret: str) -> str:
    combined = f"{timestamp}{payload_str}{secret}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def get_headers(
    api_key: str, api_secret: str, session_token: str, payload_str: str = ""
) -> Dict[str, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    checksum = compute_signature(timestamp, payload_str, api_secret)
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-AppKey": api_key,
        "X-SessionToken": session_token,
        "SessionToken": session_token,
        "X-Timestamp": timestamp,
        "X-Checksum": f"token {checksum}",
    }


def call_endpoint(
    client: httpx.Client,
    method: str,
    path: str,
    api_key: str,
    api_secret: str,
    session_token: str,
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    desc: str = "",
) -> None:
    url = f"{BREEZE_BASE_URL}/{path}" if not path.startswith("http") else path
    body_json = json.dumps(body, separators=(",", ":")) if body else ""
    headers = get_headers(api_key, api_secret, session_token, body_json)

    print("\n" + "=" * 80)
    print(f"TEST: {desc or path}")
    print(f"REQUEST: {method} {url}")
    if params:
        print(f"PARAMS: {params}")
    if body:
        print(f"BODY: {body_json}")
    print("-" * 80)

    try:
        resp = client.request(
            method=method,
            url=url,
            headers=headers,
            content=body_json.encode("utf-8") if body_json else None,
            params=params,
            timeout=15.0,
        )
        print(f"STATUS: {resp.status_code}")
        print(f"RESPONSE HEADERS: {dict(resp.headers)}")
        try:
            parsed = resp.json()
            print("RESPONSE JSON:")
            print(json.dumps(parsed, indent=2))
        except Exception:
            print("RAW TEXT RESPONSE:")
            print(resp.text)
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Inspect raw ICICI Breeze API responses")
    parser.add_argument("--api-key", help="ICICI Breeze API Key (optional, defaults to DB)")
    parser.add_argument("--api-secret", help="ICICI Breeze API Secret (optional, defaults to DB)")
    parser.add_argument("--session-token", help="ICICI Breeze Session Token (optional, defaults to DB)")
    args = parser.parse_args()

    api_key = args.api_key
    api_secret = args.api_secret
    session_token = args.session_token

    if not (api_key and api_secret and session_token):
        print("Reading credentials from database...")
        db = SessionLocal()
        try:
            cred = (
                db.query(BrokerCredential)
                .filter(BrokerCredential.provider_name == "icici_breeze")
                .first()
            )
            if not cred:
                print("ERROR: No icici_breeze credential found in database!")
                sys.exit(1)
            api_key = api_key or cred.api_key
            api_secret = api_secret or crud_broker.get_decrypted_secret(cred)
            session_token = session_token or crud_broker.get_decrypted_token(cred)
        finally:
            db.close()

    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "****"
    masked_tok = f"{session_token[:4]}...{session_token[-4:]}" if session_token and len(session_token) > 8 else "****"
    print(f"Using API Key: {masked_key}")
    print(f"Using Session Token: {masked_tok}")
    print(f"API Secret Set: {bool(api_secret)}")

    now_utc = datetime.now(timezone.utc)
    today_iso_start = now_utc.strftime("%Y-%m-%dT00:00:00.000Z")
    today_iso_end = now_utc.strftime("%Y-%m-%dT23:59:59.000Z")
    
    days_30_ago = (now_utc - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
    days_365_ago = (now_utc - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00.000Z")
    
    today_date_str = now_utc.strftime("%Y-%m-%d")
    days_30_date_str = (now_utc - timedelta(days=30)).strftime("%Y-%m-%d")

    with httpx.Client() as client:
        # 1. Customer Details (Check Session Validity)
        print("\n--- 1. Testing Session Auth (/customerdetails) ---")
        cust_body = {"SessionToken": session_token, "AppKey": api_key}
        cust_body_json = json.dumps(cust_body, separators=(",", ":"))
        cust_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        cust_resp = client.request(
            "GET",
            f"{BREEZE_BASE_URL}/customerdetails",
            headers=cust_headers,
            content=cust_body_json.encode("utf-8"),
            timeout=15.0,
        )
        print(f"Customer Details Status: {cust_resp.status_code}")
        try:
            cust_json = cust_resp.json()
            print("Customer Details JSON:", json.dumps(cust_json, indent=2))
            if cust_json.get("Status") == 200 and cust_json.get("Success"):
                fresh_token = cust_json["Success"].get("session_token")
                if fresh_token:
                    session_token = fresh_token
                    print(f"Adopted session token from customerdetails: {session_token[:4]}...{session_token[-4:]}")
        except Exception:
            print("Customer Details Text:", cust_resp.text)

        # 2. Portfolio Holdings (NSE and BSE)
        print("\n--- 2. Testing Portfolio Holdings (/portfolioholdings) ---")
        call_endpoint(
            client, "GET", "portfolioholdings", api_key, api_secret, session_token,
            body={"exchange_code": "NSE"},
            desc="Portfolio Holdings (NSE) with body"
        )
        call_endpoint(
            client, "GET", "portfolioholdings", api_key, api_secret, session_token,
            body={"exchange_code": "BSE"},
            desc="Portfolio Holdings (BSE) with body"
        )

        # 3. Demat Holdings / Other Holdings
        print("\n--- 3. Testing Demat Holdings (/dematholdings) ---")
        call_endpoint(
            client, "GET", "dematholdings", api_key, api_secret, session_token,
            body={},
            desc="Demat Holdings (empty body)"
        )

        # 4. Orders / Order List (/order) - Notice: ICICI Breeze strictly limits /order to <= 10 days!
        print("\n--- 4. Testing Order List Endpoints (/order) ---")
        days_4_ago = (now_utc - timedelta(days=4)).strftime("%Y-%m-%dT00:00:00.000Z")
        call_endpoint(
            client, "GET", "order", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": today_iso_start, "to_date": today_iso_end},
            desc="Order List (/order) - Today (NSE)"
        )
        call_endpoint(
            client, "GET", "order", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": days_4_ago, "to_date": today_iso_end},
            desc="Order List (/order) - Last 4 Days (NSE)"
        )
        call_endpoint(
            client, "GET", "order", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": days_30_ago, "to_date": today_iso_end},
            desc="Order List (/order) - Last 30 Days (NSE - Expected error: > 10 days)"
        )

        # 5. Trades / Trade List (/trades) - Supports historical ranges up to multiple years!
        print("\n--- 5. Testing Trades Endpoints (/trades) ---")
        days_7_ago = (now_utc - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000Z")
        call_endpoint(
            client, "GET", "trades", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": today_iso_start, "to_date": today_iso_end},
            desc="Trades (/trades) - Today (NSE)"
        )
        call_endpoint(
            client, "GET", "trades", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": days_7_ago, "to_date": today_iso_end},
            desc="Trades (/trades) - Last 7 Days (NSE)"
        )
        call_endpoint(
            client, "GET", "trades", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": days_30_ago, "to_date": today_iso_end},
            desc="Trades (/trades) - Last 30 Days (NSE)"
        )
        call_endpoint(
            client, "GET", "trades", api_key, api_secret, session_token,
            body={"exchange_code": "NSE", "from_date": days_365_ago, "to_date": today_iso_end},
            desc="Trades (/trades) - Last 365 Days (NSE)"
        )
        call_endpoint(
            client, "GET", "trades", api_key, api_secret, session_token,
            body={"exchange_code": "BSE", "from_date": days_365_ago, "to_date": today_iso_end},
            desc="Trades (/trades) - Last 365 Days (BSE)"
        )


if __name__ == "__main__":
    main()
