import logging
import os
from datetime import date, timedelta
from typing import Dict, List, Optional, Union

import requests
import urllib3

# Suppress only the InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def download_file(
    url: str, dest_path: str, log: Optional[logging.Logger] = None
) -> bool:
    """
    Downloads a file from a URL to a destination path.
    Returns True if successful, False otherwise.
    """
    if log:
        log.info(f"Downloading {url}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        # nosec B501: SSL verification disabled for NSDL/BSE/NSE with cert issues
        response = requests.get(
            url, stream=True, verify=False, headers=headers, timeout=30
        )
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        if log:
            log.info(f"Saved to {dest_path}")
        return True
    except Exception as e:
        if log:
            log.warning(f"Download failed for {url}: {e}")
        return False

def get_latest_trading_date() -> date:
    """Returns the latest potential trading date (today or previous weekday)."""
    d = date.today()
    if d.weekday() == 5:  # Sat
        d -= timedelta(days=1)
    elif d.weekday() == 6:  # Sun
        d -= timedelta(days=2)
    return d

def decrement_trading_day(d: date) -> date:
    """Returns the previous trading day (skipping weekends)."""
    d -= timedelta(days=1)
    while d.weekday() > 4:  # Sat=5, Sun=6
        d -= timedelta(days=1)
    return d

def get_dynamic_urls(d: date) -> Dict[str, Union[str, List[str]]]:
    """Generates URLs for a specific trading date."""
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

def download_all_sources(
    temp_dir: str, log: Optional[logging.Logger] = None
) -> Dict[str, str]:
    """Download all required data sources. Returns dict of source -> filepath."""
    files: Dict[str, str] = {}
    candidate_dates = []
    current_d = get_latest_trading_date()
    candidate_dates.append(current_d)
    for _ in range(2):
        current_d = decrement_trading_day(current_d)
        candidate_dates.append(current_d)

    if log:
        log.info(f"Trying dates: {[d.isoformat() for d in candidate_dates]}")

    required_sources = [
        "nsdl", "bse_public", "bse_equity", "bse_debt",
        "nse_debt", "nse_equity", "bse_index", "icici"
    ]

    for source in required_sources:
        for d in candidate_dates:
            urls = get_dynamic_urls(d).get(source)
            if not urls:
                continue

            if isinstance(urls, str):
                urls = [urls]

            success = False
            for url in urls:
                filename = url.split("/")[-1]
                dest = os.path.join(temp_dir, filename)

                if download_file(url, dest, log):
                    files[source] = dest
                    success = True
                    break
            if success:
                break

        if source not in files and log:
            log.warning(f"Could not download {source} after trying all dates.")

    return files

def process_all_sources(
    seeder, files: Dict[str, str], log: Optional[logging.Logger] = None
) -> None:
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
