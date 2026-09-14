from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session


from app import models
from app.core.dependencies import get_current_active_user
from app.crud.crud_broker import crud_broker
from app.db.session import get_db
from app.schemas.broker import (
    BrokerAuthenticateRequest,
    BrokerAuthUrlResponse,
    BrokerCredentialResponse,
    BrokerCredentialSave,
)
from app.services.providers.icici_breeze_provider import IciciBreezeProvider
from app.services.providers.zerodha_provider import ZerodhaKiteProvider


router = APIRouter()


@router.get("/credentials", response_model=List[BrokerCredentialResponse])
def get_broker_credentials(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Retrieve all configured broker integration statuses for current user."""
    creds = crud_broker.get_all_by_user(db, user_id=current_user.id)
    now = datetime.now(timezone.utc)
    res = []
    for c in creds:
        is_auth = bool(
            c.encrypted_access_token
            and (c.token_expires_at is None or c.token_expires_at > now)
        )
        res.append(
            BrokerCredentialResponse(
                id=c.id,
                provider_name=c.provider_name,
                api_key=c.api_key,
                is_active=c.is_active,
                is_authenticated=is_auth,
                token_issued_at=c.token_issued_at,
                token_expires_at=c.token_expires_at,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return res


@router.post("/credentials", response_model=BrokerCredentialResponse)
def save_broker_credentials(
    cred_in: BrokerCredentialSave,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Save or update API key & secret for a broker integration."""
    provider = cred_in.provider_name.lower().strip()
    if provider not in ["icici_breeze", "zerodha_kite"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported broker provider: {cred_in.provider_name}",
        )

    db_obj = crud_broker.save_credentials(
        db,
        user_id=current_user.id,
        provider_name=provider,
        api_key=cred_in.api_key.strip(),
        api_secret=cred_in.api_secret.strip(),
    )

    now = datetime.now(timezone.utc)
    is_auth = bool(
        db_obj.encrypted_access_token
        and (db_obj.token_expires_at is None or db_obj.token_expires_at > now)
    )

    return BrokerCredentialResponse(
        id=db_obj.id,
        provider_name=db_obj.provider_name,
        api_key=db_obj.api_key,
        is_active=db_obj.is_active,
        is_authenticated=is_auth,
        token_issued_at=db_obj.token_issued_at,
        token_expires_at=db_obj.token_expires_at,
        created_at=db_obj.created_at,
        updated_at=db_obj.updated_at,
    )


@router.get("/icici/login-url", response_model=BrokerAuthUrlResponse)
def get_icici_login_url(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Generates the ICICI Direct login URL for the configured API Key."""
    cred = crud_broker.get_by_user_and_provider(
        db, user_id=current_user.id, provider_name="icici_breeze"
    )
    if not cred or not cred.api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ICICI Breeze credentials not found. Please save API Key first.",
        )

    url = IciciBreezeProvider.get_login_url(cred.api_key)
    return BrokerAuthUrlResponse(provider_name="icici_breeze", login_url=url)


@router.get("/icici/callback", response_class=HTMLResponse)
def icici_broker_callback(
    apisession: str = Query(..., alias="apisession"),
):
    """Callback landing page for ICICI Breeze OAuth redirect."""
    html_content = f"""
    <!质html>
    <html>
    <head>
        <title>ICICI Breeze Session Token</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 40px; text-align: center; }}
            .card {{ background: white; max-width: 500px; margin: 0 auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            h2 {{ color: #166534; margin-top: 0; }}
            .token-box {{ background: #f0fdf4; border: 2px dashed #22c55e; padding: 15px; font-size: 20px; font-weight: bold; color: #15803d; border-radius: 8px; margin: 20px 0; word-break: break-all; }}
            p {{ color: #4b5563; font-size: 14px; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>✅ ICICI Breeze Login Successful!</h2>
            <p>Your ICICI Breeze Session Token (API Session) is:</p>
            <div class="token-box">{apisession}</div>
            <p>Please copy the token above and paste it into the <strong>Validate Session Token</strong> box in ArthSaarthi.</p>
        </div>
    </body>
    </html>
    """.replace("<!质html>", "<!DOCTYPE html>")
    return HTMLResponse(content=html_content)


@router.get("/zerodha/callback", response_class=HTMLResponse)
def zerodha_broker_callback(
    request_token: str = Query(..., alias="request_token"),
):
    """Callback landing page for Zerodha Kite Connect OAuth redirect."""
    html_content = f"""
    <!质html>
    <html>
    <head>
        <title>Zerodha Kite Request Token</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 40px; text-align: center; }}
            .card {{ background: white; max-width: 500px; margin: 0 auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            h2 {{ color: #0369a1; margin-top: 0; }}
            .token-box {{ background: #f0f9ff; border: 2px dashed #0284c7; padding: 15px; font-size: 20px; font-weight: bold; color: #0369a1; border-radius: 8px; margin: 20px 0; word-break: break-all; }}
            p {{ color: #4b5563; font-size: 14px; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>✅ Zerodha Kite Login Successful!</h2>
            <p>Your Zerodha Kite Request Token is:</p>
            <div class="token-box">{request_token}</div>
            <p>Please copy the token above and paste it into the <strong>Exchange & Verify Token</strong> box in ArthSaarthi.</p>
        </div>
    </body>
    </html>
    """.replace("<!质html>", "<!DOCTYPE html>")
    return HTMLResponse(content=html_content)



@router.post("/icici/authenticate", response_model=BrokerCredentialResponse)
def authenticate_icici_breeze(
    auth_in: BrokerAuthenticateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Authenticates ICICI Breeze session token and stores the session access token."""
    cred = crud_broker.get_by_user_and_provider(
        db, user_id=current_user.id, provider_name="icici_breeze"
    )
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ICICI Breeze credentials not found. Save API Key & Secret first.",
        )

    api_secret = crud_broker.get_decrypted_secret(cred)
    provider = IciciBreezeProvider(
        api_key=cred.api_key,
        session_token=auth_in.session_token,
        api_secret=api_secret,
    )

    auth_res = provider.authenticate_session(auth_in.session_token)
    if not auth_res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ICICI Breeze authentication failed: {auth_res.get('error')}",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)

    updated_cred = crud_broker.update_session_token(
        db,
        db_obj=cred,
        access_token=auth_in.session_token,
        token_issued_at=now,
        token_expires_at=expires_at,
    )

    return BrokerCredentialResponse(
        id=updated_cred.id,
        provider_name=updated_cred.provider_name,
        api_key=updated_cred.api_key,
        is_active=updated_cred.is_active,
        is_authenticated=True,
        token_issued_at=updated_cred.token_issued_at,
        token_expires_at=updated_cred.token_expires_at,
        created_at=updated_cred.created_at,
        updated_at=updated_cred.updated_at,
    )


@router.get("/zerodha/login-url", response_model=BrokerAuthUrlResponse)
def get_zerodha_login_url(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Generates the Zerodha Kite Connect login URL for the configured API Key."""
    cred = crud_broker.get_by_user_and_provider(
        db, user_id=current_user.id, provider_name="zerodha_kite"
    )
    if not cred or not cred.api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zerodha Kite credentials not found. Please save API Key first.",
        )

    url = ZerodhaKiteProvider.get_login_url(cred.api_key)
    return BrokerAuthUrlResponse(provider_name="zerodha_kite", login_url=url)


@router.post("/zerodha/authenticate", response_model=BrokerCredentialResponse)
def authenticate_zerodha_kite(
    auth_in: BrokerAuthenticateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Authenticates Zerodha Kite request_token and stores the generated session access token."""
    cred = crud_broker.get_by_user_and_provider(
        db, user_id=current_user.id, provider_name="zerodha_kite"
    )
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zerodha Kite credentials not found. Save API Key & Secret first.",
        )

    api_secret = crud_broker.get_decrypted_secret(cred)
    provider = ZerodhaKiteProvider(
        api_key=cred.api_key,
        api_secret=api_secret,
    )

    auth_res = provider.authenticate_request_token(auth_in.session_token)
    if not auth_res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zerodha Kite authentication failed: {auth_res.get('error')}",
        )

    access_token = auth_res.get("access_token")
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)

    updated_cred = crud_broker.update_session_token(
        db,
        db_obj=cred,
        access_token=access_token,
        token_issued_at=now,
        token_expires_at=expires_at,
    )

    return BrokerCredentialResponse(
        id=updated_cred.id,
        provider_name=updated_cred.provider_name,
        api_key=updated_cred.api_key,
        is_active=updated_cred.is_active,
        is_authenticated=True,
        token_issued_at=updated_cred.token_issued_at,
        token_expires_at=updated_cred.token_expires_at,
        created_at=updated_cred.created_at,
        updated_at=updated_cred.updated_at,
    )



@router.delete("/credentials/{provider_name}")
def delete_broker_credentials(
    provider_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Delete credentials for a given broker integration."""
    success = crud_broker.delete_credentials(
        db, user_id=current_user.id, provider_name=provider_name.lower().strip()
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credentials for {provider_name} not found.",
        )
    return {"message": f"Successfully deleted credentials for {provider_name}"}
