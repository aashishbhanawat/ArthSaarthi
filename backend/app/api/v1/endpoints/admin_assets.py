"""
Admin endpoints for asset management operations.
FR2.3: Manual Asset Seeding
"""
import logging
import os
import shutil
import tempfile
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, Union

import requests
import urllib3
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache.factory import get_cache_client
from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User as UserModel
from app.services.asset_seeder import AssetSeeder

# Suppress InsecureRequestWarning for NSDL connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter()
logger = logging.getLogger(__name__)

# Rate limiting constants
RATE_LIMIT_KEY = "admin:asset_sync:last_run"
RATE_LIMIT_SECONDS = 300  # 5 minutes


class AssetSyncResult(BaseModel):
    """Response model for asset sync operation."""

    status: str
    data: dict


def _check_rate_limit() -> None:
    """
    Check if the rate limit has been exceeded.
    Raises HTTPException 429 if sync was run within the last 5 minutes.
    """
    cache = get_cache_client()
    if cache is None:
        logger.warning("No cache client configured, skipping rate limit check")
        return

    last_run = cache.get(RATE_LIMIT_KEY)
    if last_run:
        last_run_time = float(last_run)
        elapsed = time.time() - last_run_time
        if elapsed < RATE_LIMIT_SECONDS:
            retry_after = int(RATE_LIMIT_SECONDS - elapsed)
            msg = f"Asset sync was run recently. Wait {retry_after} seconds."
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=msg,
                headers={"Retry-After": str(retry_after)},
            )


def _set_rate_limit() -> None:
    """Record the current time as the last sync run."""
    cache = get_cache_client()
    if cache:
        cache.set(RATE_LIMIT_KEY, str(time.time()), expire=RATE_LIMIT_SECONDS)


def _download_file(url: str, dest_path: str) -> bool:
    """
    Downloads a file from a URL to a destination path.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Downloading {url}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        # nosec B501: SSL verification disabled intentionally for NSDL/BSE/NSE
        # data sources which have known certificate issues
        response = requests.get(
            url, stream=True, verify=False, headers=headers, timeout=30  # nosec B501
        )
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded successfully: {dest_path}")
        return True
    except Exception as e:
        logger.warning(f"Download failed for {url}: {e}")
        return False


def _get_latest_trading_date() -> date:
    """Returns the latest potential trading date (today or previous weekday)."""
    d = date.today()
    if d.weekday() == 5:  # Saturday
        d -= timedelta(days=1)
    elif d.weekday() == 6:  # Sunday
        d -= timedelta(days=2)
    return d


def _decrement_trading_day(d: date) -> date:
    """Returns the previous trading day (skipping weekends)."""
    d -= timedelta(days=1)
    while d.weekday() > 4:
        d -= timedelta(days=1)
    return d


def _get_dynamic_urls(d: date) -> Dict[str, Union[str, list]]:
    """Generates URLs for a specific date."""
    dd = d.strftime("%d")
    mm = d.strftime("%m")
    yyyy = d.strftime("%Y")

    return {
        "nsdl": (
            "https://nsdl.co.in/downloadables/excel/cp-debt/"
            "Download_the_entire_list_of_Debt_Instruments_"
            f"(including_Redeemed)_as_on_{dd}.{mm}.{yyyy}.xls"
        ),
        "bse_public": "https://www.bseindia.com/downloads1/bonds_data.zip",
        "bse_equity": (
            "https://www.bseindia.com/download/BhavCopy/Equity/"
            f"BhavCopy_BSE_CM_0_0_0_{yyyy}{mm}{dd}_F_0000.CSV"
        ),
        "bse_debt": (
            "https://www.bseindia.com/download/Bhavcopy/Debt/"
            f"DEBTBHAVCOPY{dd}{mm}{yyyy}.zip"
        ),
        "nse_debt": (
            "https://nsearchives.nseindia.com/content/debt/New_debt_listing.xlsx"
        ),
        "nse_equity": (
            "https://nsearchives.nseindia.com/content/cm/"
            f"BhavCopy_NSE_CM_0_0_0_{yyyy}{mm}{dd}_F_0000.csv.zip"
        ),
        "bse_index": (
            "https://www.bseindia.com/bsedata/Index_Bhavcopy/"
            f"INDEXSummary_{dd}{mm}{yyyy}.csv"
        ),
        "icici": (
            "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
        ),
    }


def _download_all_sources(temp_dir: str) -> Dict[str, str]:
    """Download all required data sources. Returns dict of source -> filepath."""
    files: Dict[str, str] = {}

    # Prepare candidate dates (Today, T-1, T-2)
    candidate_dates = []
    current_d = _get_latest_trading_date()
    candidate_dates.append(current_d)
    for _ in range(2):
        current_d = _decrement_trading_day(current_d)
        candidate_dates.append(current_d)

    logger.info(f"Trying dates: {[d.isoformat() for d in candidate_dates]}")

    required_sources = [
        "nsdl", "bse_public", "bse_equity", "bse_debt",
        "nse_debt", "nse_equity", "bse_index", "icici"
    ]

    for source in required_sources:
        for d in candidate_dates:
            urls = _get_dynamic_urls(d)
            url = urls.get(source)
            if not url:
                continue

            if isinstance(url, list):
                url = url[0]

            filename = url.split("/")[-1]
            dest = os.path.join(temp_dir, filename)

            if _download_file(url, dest):
                files[source] = dest
                break

        if source not in files:
            logger.warning(f"Could not download {source} after trying all dates.")

    return files


def _process_all_sources(seeder: AssetSeeder, files: Dict[str, str]) -> None:
    """Process all downloaded files through the seeder."""
    # Phase 1: Master Debt Lists
    if "nsdl" in files:
        seeder.process_nsdl_file(files["nsdl"])
    if "bse_public" in files:
        seeder.process_bse_public_debt(files["bse_public"])

    # Phase 2: Exchange Bhavcopy
    if "bse_equity" in files:
        seeder.process_bse_equity_bhavcopy(files["bse_equity"])
    if "nse_equity" in files:
        seeder.process_nse_equity_bhavcopy(files["nse_equity"])

    # Phase 3: Specialized Debt
    if "nse_debt" in files:
        seeder.process_nse_daily_debt(files["nse_debt"])
    if "bse_debt" in files:
        seeder.process_bse_debt_bhavcopy(files["bse_debt"])

    # Phase 4: Market Indices
    if "bse_index" in files:
        seeder.process_bse_index(files["bse_index"])

    # Phase 5: Fallback
    if "icici" in files:
        seeder.process_icici_fallback(files["icici"])


@router.post(
    "/sync",
    response_model=AssetSyncResult,
    status_code=status.HTTP_200_OK,
    summary="Trigger Asset Master Sync",
    description="Downloads and parses asset data from exchanges. Admin only.",
)
def sync_assets(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user),
) -> Any:
    """
    Trigger a manual sync of the asset master database.

    Downloads and processes asset data from NSDL, BSE, NSE, and other sources.
    Returns a summary of newly added and updated assets.

    Rate limited to once every 5 minutes.
    """
    # Check rate limit
    _check_rate_limit()

    # Set rate limit timestamp before starting
    _set_rate_limit()

    logger.info(f"Asset sync triggered by admin user: {current_user.email}")

    try:
        # Initialize the asset seeder
        seeder = AssetSeeder(db=db, debug=False)

        # Get initial counts
        initial_created = seeder.created_count
        initial_skipped = seeder.skipped_count

        # Create temp directory for downloads
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")

        try:
            # Download all data sources
            files = _download_all_sources(temp_dir)
            logger.info(f"Downloaded {len(files)} of 8 sources")

            # Process all files
            _process_all_sources(seeder, files)

            # Commit changes
            db.commit()

        finally:
            # Cleanup temp files
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir: {e}")

        # Calculate results
        newly_added = seeder.created_count - initial_created
        updated = seeder.skipped_count - initial_skipped

        result = {
            "total_processed": newly_added + updated,
            "newly_added": newly_added,
            "updated": updated,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(f"Asset sync completed: {result}")

        return AssetSyncResult(status="success", data=result)

    except Exception as e:
        logger.error(f"Asset sync failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Asset sync failed: {str(e)}",
        )
