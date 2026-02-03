"""
FMV 2018 Seeder Service.
Downloads and parses official BSE/AMFI data for Jan 31, 2018 to populate fmv_2018.
"""

import io
import logging
import zipfile
from decimal import Decimal
from typing import Dict

import pandas as pd
import requests
from sqlalchemy.orm import Session

from app.models import Asset

logger = logging.getLogger(__name__)

# Official data source URLs for Jan 31, 2018
BSE_BHAVCOPY_URL = (
    "https://www.bseindia.com/download/BhavCopy/Equity/EQ_ISINCODE_310118.zip"
)
AMFI_NAV_URL = (
    "https://www.amfiindia.com/uploads/NAV_All_31_Jan2018_713f553045.xls"
)


class FMV2018Seeder:
    """Seeder to populate fmv_2018 from official BSE/AMFI data."""

    def __init__(self, db: Session):
        self.db = db
        self.updated_count = 0
        self.skipped_count = 0
        self.errors: list[str] = []

    def seed_all(self, overwrite: bool = False) -> Dict[str, int]:
        """
        Download and process both BSE and AMFI data.
        Returns counts of updated and skipped assets.
        If overwrite is True, updates existing non-null FMV values.
        """
        logger.info("Starting FMV 2018 seeding from official sources...")

        # 1. Process BSE Bhavcopy (Stocks)
        try:
            bse_prices = self._download_and_parse_bse()
            logger.info(f"Parsed {len(bse_prices)} prices from BSE Bhavcopy")
            self._update_assets_from_prices(
                bse_prices, source="BSE", overwrite=overwrite
            )
        except Exception as e:
            logger.error(f"Failed to process BSE data: {e}")
            self.errors.append(f"BSE: {str(e)}")

        # 2. Process AMFI NAV (Mutual Funds)
        try:
            amfi_navs = self._download_and_parse_amfi()
            logger.info(f"Parsed {len(amfi_navs)} NAVs from AMFI")
            self._update_assets_from_prices(
                amfi_navs, source="AMFI", overwrite=overwrite
            )
        except Exception as e:
            logger.error(f"Failed to process AMFI data: {e}")
            self.errors.append(f"AMFI: {str(e)}")

        # Commit all changes
        self.db.commit()

        logger.info(
            f"FMV 2018 seeding complete: {self.updated_count} updated, "
            f"{self.skipped_count} skipped"
        )

        return {
            "updated": self.updated_count,
            "skipped": self.skipped_count,
            "errors": len(self.errors),
        }

    def _download_and_parse_bse(self) -> Dict[str, Decimal]:
        """
        Download BSE Bhavcopy ZIP and parse closing prices.
        Returns dict of ISIN -> closing price.
        """
        logger.info(f"Downloading BSE Bhavcopy from {BSE_BHAVCOPY_URL}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/91.0 Safari/537.36"
            )
        }

        response = requests.get(
            BSE_BHAVCOPY_URL, headers=headers, timeout=60, verify=False
        )
        response.raise_for_status()

        prices: Dict[str, Decimal] = {}

        # Extract ZIP and parse CSV
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for filename in zf.namelist():
                if filename.endswith(".CSV") or filename.endswith(".csv"):
                    with zf.open(filename) as f:
                        df = pd.read_csv(f)

                        # BSE Bhavcopy columns:
                        # SC_CODE, SC_NAME, ISIN_CODE, CLOSE, HIGH, LOW
                        for _, row in df.iterrows():
                            isin = str(row.get("ISIN_CODE", "")).strip()
                            high_price = row.get("HIGH")

                            if isin and high_price and pd.notna(high_price):
                                try:
                                    prices[isin] = Decimal(str(high_price))
                                except Exception:
                                    pass

        return prices

    def _download_and_parse_amfi(self) -> Dict[str, Decimal]:
        """
        Download AMFI NAV Excel and parse NAV values.
        Returns dict of scheme_code -> NAV.
        """
        logger.info(f"Downloading AMFI NAV from {AMFI_NAV_URL}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/91.0 Safari/537.36"
            )
        }

        response = requests.get(
            AMFI_NAV_URL, headers=headers, timeout=60, verify=False
        )
        response.raise_for_status()

        navs: Dict[str, Decimal] = {}

        # AMFI serves HTML with .xls extension - parse as HTML
        try:
            # Try reading as HTML table
            # header=None to read everything as data first, then find the header
            tables = pd.read_html(io.BytesIO(response.content), header=None)
            if tables:
                df = tables[0]  # First table
                # Reset columns to simple integer index to avoid MultiIndex issues
                df.columns = range(df.shape[1])
            else:
                logger.warning("No tables found in AMFI HTML")
                return navs
        except Exception as html_err:
            logger.warning(f"HTML parse failed, trying Excel: {html_err}")
            # Fallback to Excel parsing
            try:
                df = pd.read_excel(io.BytesIO(response.content), engine="xlrd", header=None)
            except Exception as excel_err:
                 logger.error(f"Excel parse failed: {excel_err}")
                 return navs

        target_col_idx = 0
        
        # Parse interleaved rows (Scheme Name in row i, NAV in row i+1)
        # Based on observation: Col 0 contains both Scheme Name and NAV alternating
        for i in range(len(df) - 1):
            val1 = str(df.iloc[i, target_col_idx]).strip()
            val2 = str(df.iloc[i+1, target_col_idx]).strip()

            # Logic: If val2 is a float (NAV) and val1 is a string (Name), it's a pair.
            # Avoid cases where val1 is also a number (unlikely for Name)
            
            is_val2_nav = False
            nav_val = None
            
            try:
                # remove commas and 'N.A.'
                val2_clean = val2.replace(',', '').replace('N.A.', '').strip()
                if val2_clean:
                    nav_val = Decimal(val2_clean)
                    # Sanity check: NAV shouldn't be a huge integer like a scheme code, 
                    # but some NAVs can be high. 100,000 is a safe upper bound for 2018 NAVs usually,
                    # but MRF stock sort of prices don't apply to MF units usually. 
                    # Let's check format: usually has a decimal point or is < 100000.
                    if 0 < nav_val < 200000: 
                        is_val2_nav = True
            except Exception:
                pass
            
            if is_val2_nav and val1 and not val1.replace('.','',1).isdigit():
                # val1 is likely the name
                scheme_name = val1
                navs[scheme_name] = nav_val
                # We could skip i+1, but the loop handles it (next i will treat NAV as val1, next row as val2)
                # Next iteration: val1=NAV, val2=NextName (String). Won't trigger.
                pass

        return navs

    def _update_assets_from_prices(
        self, prices: Dict[str, Decimal], source: str, overwrite: bool = False
    ) -> None:
        """
        Update fmv_2018 for assets matching the prices dict.
        For BSE: match by ISIN
        For AMFI: match by Name (exact match, case-insensitive)
        """
        if source == "BSE":
            # Match by ISIN
            for isin, price in prices.items():
                asset = self.db.query(Asset).filter(Asset.isin == isin).first()
                if asset:
                    if asset.fmv_2018 is None or overwrite:
                        asset.fmv_2018 = price
                        self.updated_count += 1
                    else:
                        self.skipped_count += 1

        elif source == "AMFI":
            # Match by Name for mutual funds (since file lacks Scheme Codes)
            # Use a map of standardized names from DB to avoid N queries
            # Or iterate prices and query.
            # Optimization: Load all Mutual Funds data first
            
            db_assets = self.db.query(Asset).filter(
                Asset.asset_type.in_(["MUTUAL_FUND", "MUTUAL FUND", "Mutual Fund"])
            ).all()
            
            # Map normalized name to asset
            name_map = {a.name.strip().upper(): a for a in db_assets if a.name}
            
            for scheme_name, nav in prices.items():
                norm_name = scheme_name.strip().upper()
                asset = name_map.get(norm_name)
                
                if asset:
                    if asset.fmv_2018 is None or overwrite:
                        asset.fmv_2018 = nav
                        self.updated_count += 1
                    else:
                         self.skipped_count += 1
                else:
                    # Optional: fuzzy match or log missing
                    pass
