import logging
import threading
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Asset
from app.services.asset_seeder import AssetSeeder
from app.db.initial_data import seed_interest_rates
import tempfile
import os
import shutil
import requests
import urllib3
from datetime import date, timedelta
from typing import Dict, Union

# Suppress InsecureRequestWarning for NSDL connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def _get_latest_trading_date() -> date:
    d = date.today()
    if d.weekday() == 5:  # Saturday
        d -= timedelta(days=1)
    elif d.weekday() == 6:  # Sunday
        d -= timedelta(days=2)
    return d

def _decrement_trading_day(d: date) -> date:
    d -= timedelta(days=1)
    while d.weekday() > 4:
        d -= timedelta(days=1)
    return d

def _get_dynamic_urls(d: date) -> Dict[str, Union[str, list]]:
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

def _download_file(url: str, dest_path: str) -> bool:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = requests.get(
            url, stream=True, verify=False, headers=headers, timeout=30
        )
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning(f"Download failed for {url}: {e}")
        return False

def _run_initial_seeding():
    """Actually performs the seeding logic in a thread."""
    from app.api.v1.endpoints.system import _seeding_state, SeedingStatus
    logger.info("Background initial seeding thread started.")
    _seeding_state["status"] = SeedingStatus.IN_PROGRESS
    _seeding_state["progress"] = 10
    _seeding_state["message"] = "Fetching reference instruments lists..."
    
    db = SessionLocal()
    try:
        # 1. Seed Interest Rates
        seed_interest_rates(db)
        db.commit()
        
        # 2. Sync Assets
        seeder = AssetSeeder(db=db, debug=False)
        temp_dir = tempfile.mkdtemp()
        try:
            candidate_dates = []
            current_d = _get_latest_trading_date()
            candidate_dates.append(current_d)
            for _ in range(2):
                current_d = _decrement_trading_day(current_d)
                candidate_dates.append(current_d)

            required_sources = [
                "nsdl", "bse_public", "bse_equity", "bse_debt",
                "nse_debt", "nse_equity", "bse_index", "icici"
            ]

            files = {}
            for source in required_sources:
                for d in candidate_dates:
                    url = _get_dynamic_urls(d).get(source)
                    if not url: continue
                    filename = url.split("/")[-1]
                    dest = os.path.join(temp_dir, filename)
                    if _download_file(url, dest):
                        files[source] = dest
                        break
            
            # Process
            if "nsdl" in files: seeder.process_nsdl_file(files["nsdl"])
            if "bse_public" in files: seeder.process_bse_public_debt(files["bse_public"])
            if "bse_equity" in files: seeder.process_bse_equity_bhavcopy(files["bse_equity"])
            if "nse_equity" in files: seeder.process_nse_equity_bhavcopy(files["nse_equity"])
            if "nse_debt" in files: seeder.process_nse_daily_debt(files["nse_debt"])
            if "bse_debt" in files: seeder.process_bse_debt_bhavcopy(files["bse_debt"])
            if "bse_index" in files: seeder.process_bse_index(files["bse_index"])
            if "icici" in files: seeder.process_icici_fallback(files["icici"])
            
            db.commit()
            _seeding_state["status"] = SeedingStatus.COMPLETE
            _seeding_state["progress"] = 100
            _seeding_state["message"] = "Background initial seeding completed successfully!"
            logger.info("Background initial seeding completed successfully.")
        finally:
            shutil.rmtree(temp_dir)
    except Exception as e:
        _seeding_state["status"] = SeedingStatus.FAILED
        _seeding_state["error"] = str(e)
        logger.error(f"Background initial seeding failed: {e}", exc_info=True)
    finally:
        db.close()

def check_and_seed_on_startup():
    """Checks if database is empty and triggers background seeding if so."""
    from app.api.v1.endpoints.system import _seeding_state, SeedingStatus
    db = SessionLocal()
    try:
        count = db.query(Asset).count()
        if count < 10000:
            logger.info(f"Assets table has {count} assets (<10000). Triggering background seeding...")
            _seeding_state["status"] = SeedingStatus.IN_PROGRESS
            _seeding_state["message"] = "Preparing to download and seed data..."
            threading.Thread(target=_run_initial_seeding, daemon=True).start()
        else:
            logger.info(f"Database already has {count} assets. Skipping initial seeding.")
            _seeding_state["status"] = SeedingStatus.COMPLETE
            _seeding_state["progress"] = 100
            _seeding_state["message"] = "Asset database ready"
    except Exception as e:
        logger.error(f"Error during startup seeding check: {e}")
    finally:
        db.close()
