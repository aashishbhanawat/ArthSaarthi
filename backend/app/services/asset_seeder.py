import collections
import logging
import re
import zipfile
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional, Set, Tuple

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.schemas.bond import BondCreate
from app.schemas.enums import BondType

# Setup logger
logger = logging.getLogger(__name__)


class AssetSeeder:
    def __init__(self, db: Session, debug: bool = False):
        self.db = db
        self.debug = debug
        self.created_count = 0
        self.skipped_count = 0
        self.skipped_series_counts = collections.Counter()

        # Caches to prevent duplicates
        self.existing_isins: Set[str] = set()
        self.existing_tickers: Set[str] = set()
        self.existing_composite_keys: Set[Tuple[str, str, str]] = set()

        self._load_existing_assets()

    def _load_existing_assets(self):
        """Loads existing assets into memory to minimize DB queries."""
        # Check if tables exist first
        from sqlalchemy import inspect
        inspector = inspect(self.db.bind)
        if not inspector.has_table("assets"):
            return

        assets = self.db.query(
            models.Asset.isin,
            models.Asset.ticker_symbol,
            models.Asset.name,
            models.Asset.asset_type,
            models.Asset.currency
        ).all()

        for isin, ticker, name, atype, currency in assets:
            if isin:
                self.existing_isins.add(isin)
            if ticker:
                self.existing_tickers.add(ticker)
            self.existing_composite_keys.add((name, atype, currency))

        if self.debug:
            print(
                f"[DEBUG] Loaded {len(self.existing_isins)} ISINs, "
                f"{len(self.existing_tickers)} Tickers."
            )

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parses a date from various formats."""
        if pd.isna(value) or value == '':
            return None
        try:
            if isinstance(value, (datetime, date)):
                return value if isinstance(value, date) else value.date()
            # Try parsing string
            return pd.to_datetime(value, dayfirst=True).date()
        except Exception:
            return None

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parses a decimal value."""
        if pd.isna(value) or value == '':
            return None
        try:
            # Handle percentage strings if present (e.g. "8.5%")
            if isinstance(value, str):
                value = value.replace('%', '').replace(',', '').strip()
            return Decimal(str(value))
        except Exception:
            return None

    def _create_asset(self, data: dict) -> bool:
        """Creates an asset and optionally a bond record."""
        # Duplicate checks
        isin = data.get("isin")
        ticker = data.get("ticker_symbol")
        name = data.get("name")
        asset_type = data.get("asset_type")

        if isin and isin in self.existing_isins:
            return False
        if ticker and ticker in self.existing_tickers:
            # Fallback: if ticker exists but ISIN is different,
            # we might have a collision.
            # But usually ticker uniqueness is strict.
            return False

        composite_key = (name, asset_type, "INR")
        if composite_key in self.existing_composite_keys:
            return False

        try:
            asset_in = schemas.AssetCreate(
                name=name,
                ticker_symbol=ticker,
                isin=isin,
                asset_type=asset_type,
                currency="INR",
                exchange=data.get("exchange", "N/A")
            )
            asset = crud.asset.create(db=self.db, obj_in=asset_in)

            if asset_type == "BOND" and data.get("bond_type"):
                bond_in = BondCreate(
                    asset_id=asset.id,
                    bond_type=data["bond_type"],
                    maturity_date=data.get("maturity_date") or date(1970, 1, 1),
                    isin=isin,
                    face_value=data.get("face_value"),
                    coupon_rate=data.get("coupon_rate"),
                    # interest_frequency logic can be added if data available
                )
                crud.bond.create(db=self.db, obj_in=bond_in)

            # Update caches
            if isin:
                self.existing_isins.add(isin)
            self.existing_tickers.add(ticker)
            self.existing_composite_keys.add(composite_key)
            self.created_count += 1
            return True
        except IntegrityError:
            self.db.rollback()
            self.skipped_count += 1
            return False
        except Exception as e:
            if self.debug:
                print(f"[ERROR] Failed to create asset {name}: {e}")
            self.skipped_count += 1
            return False

    # --- Phase 1: Master Debt Lists ---
    def process_nsdl_file(self, filepath: str):
        """Phase 1 Source 1: NSDL Debt Instruments (TSV/XLS)."""
        print(f"Processing NSDL file: {filepath}")
        try:
            # Try reading as CSV with tab separator (as discovered)
            df = pd.read_csv(
                filepath, sep='\t', on_bad_lines='skip', encoding='latin1'
            )
        except Exception:
            try:
                 df = pd.read_excel(filepath)
            except Exception as e:
                print(f"Failed to read NSDL file: {e}")
                return

        for _, row in df.iterrows():
            isin = str(row.get('ISIN', '')).strip()
            if not isin or pd.isna(isin):
                continue

            # Use ISIN as ticker if no other identifier, but usually ISIN
            # is the key here. We map NSDL -> BOND definitively.
            name = str(row.get('NAME_OF_THE_INSTRUMENT', '')).strip()
            if not name:
                name = f"Bond {isin}"

            maturity_date = self._parse_date(row.get('REDEMPTION'))
            face_value = self._parse_decimal(row.get('FACE_VALUE'))
            coupon_rate = self._parse_decimal(row.get('COUPON_RATE'))

            data = {
                "isin": isin,
                "ticker_symbol": isin, # Fallback ticker
                "name": name,
                "asset_type": "BOND",
                "bond_type": BondType.CORPORATE, # Default, could be refined
                "maturity_date": maturity_date,
                "face_value": face_value,
                "coupon_rate": coupon_rate,
                "exchange": "N/A" # OTC / NSDL
            }
            self._create_asset(data)

    def process_bse_public_debt(self, filepath: str):
        """Phase 1 Source 2: BSE Public Bond (XLSX inside Zip)."""
        print(f"Processing BSE Public Debt: {filepath}")
        try:
            with zipfile.ZipFile(filepath) as z:
                for filename in z.namelist():
                    if filename.endswith(".xlsx"):
                        with z.open(filename) as f:
                            df = pd.read_excel(f, engine='openpyxl')
                            self._process_bse_public_debt_df(df)
        except Exception as e:
            print(f"Error processing BSE Public Debt zip: {e}")

    def _process_bse_public_debt_df(self, df: pd.DataFrame):
        for _, row in df.iterrows():
            isin = str(row.get('ISIN', '')).strip()
            ticker = str(row.get('Scrip_ Code', '')).strip()
            name = str(row.get('Scrip_Long_Name', '')).strip()

            if not isin or not ticker:
                continue

            maturity_date = self._parse_date(row.get('Conversion_Date'))
            face_value = self._parse_decimal(row.get('Scrip_Face_Value'))
            coupon_rate = self._parse_decimal(row.get('Interest_Rate'))

            data = {
                "isin": isin,
                "ticker_symbol": ticker,
                "name": name,
                "asset_type": "BOND",
                "bond_type": BondType.CORPORATE, # Mostly corporate public issues
                "maturity_date": maturity_date,
                "face_value": face_value,
                "coupon_rate": coupon_rate,
                "exchange": "BSE"
            }
            self._create_asset(data)

    # --- Phase 2: Exchange Bhavcopy ---
    def process_bse_equity_bhavcopy(self, filepath: str):
        """Phase 2 Source 3: BSE Equity Bhavcopy (CSV)."""
        print(f"Processing BSE Equity Bhavcopy: {filepath}")
        try:
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                self._process_bse_equity_row(row)
        except Exception as e:
            print(f"Error reading BSE Equity CSV: {e}")

    def _process_bse_equity_row(self, row: pd.Series):
        isin = str(row.get('ISIN', '')).strip()
        ticker = str(row.get('TckrSymb', '')).strip()
        series = str(row.get('SctySrs', '')).strip().upper()
        name = str(row.get('FinInstrmNm', '')).strip()

        if not isin or not ticker:
            return

        # Classification based on Series (SctySrs)
        asset_type = None
        bond_type = None

        if series in ['A', 'B', 'T', 'X', 'XT', 'Z', 'P']: # Standard Equity Series
            asset_type = "STOCK"
        elif series == 'E':
            asset_type = "ETF" # Or STOCK with specific flag
        elif series == 'G':
            asset_type = "BOND"
            bond_type = BondType.GOVERNMENT
        elif series == 'F':
            asset_type = "BOND"
            bond_type = BondType.CORPORATE
        else:
             # Unknown series, maybe skip or log?
             # For now, default to STOCK if looks like equity,
             # but better to skip if unsure.
             if series in ['M', 'MT']: # SME
                 asset_type = "STOCK"
             else:
                self.skipped_series_counts[series] += 1
                return

        data = {
            "isin": isin,
            "ticker_symbol": ticker,
            "name": name,
            "asset_type": asset_type,
            "bond_type": bond_type,
            "exchange": "BSE"
        }
        self._create_asset(data)

    def process_nse_equity_bhavcopy(self, filepath: str):
        """Phase 2 Source 4: NSE Equity Bhavcopy (CSV inside Zip)."""
        print(f"Processing NSE Equity Bhavcopy: {filepath}")
        try:
            with zipfile.ZipFile(filepath) as z:
                for filename in z.namelist():
                    if filename.endswith(".csv"):
                        with z.open(filename) as f:
                            df = pd.read_csv(f)
                            self._process_nse_equity_df(df)
        except Exception as e:
            print(f"Error processing NSE Equity Zip: {e}")

    def _process_nse_equity_df(self, df: pd.DataFrame):
        for _, row in df.iterrows():
            isin = str(row.get('ISIN', '')).strip()
            ticker = str(row.get('SYMBOL', '')).strip()
            series = str(row.get('SERIES', '')).strip().upper()
            # NSE Bhavcopy usually doesn't have full name, use Ticker as fallback
            name = ticker

            if not isin or not ticker:
                continue

            asset_type = "STOCK"
            bond_type = None

            # NSE Classification Logic
            if series in ['EQ', 'BE', 'SM', 'ST']:
                asset_type = "STOCK"
            elif series == 'GB':
                asset_type = "BOND"
                bond_type = BondType.SGB
            elif series in ['GS', 'SG', 'CG']:
                asset_type = "BOND"
                bond_type = BondType.GOVERNMENT
            elif series.startswith(('N', 'Y', 'Z')):
                # Corporate bonds often start with N, Y, Z on NSE
                asset_type = "BOND"
                bond_type = BondType.CORPORATE

            data = {
                "isin": isin,
                "ticker_symbol": ticker,
                "name": name,
                "asset_type": asset_type,
                "bond_type": bond_type,
                "exchange": "NSE"
            }
            self._create_asset(data)

    # --- Phase 3: Specialized Debt ---
    def process_nse_daily_debt(self, filepath: str):
        """Phase 3 Source 5: NSE Daily Debt (XLSX)."""
        print(f"Processing NSE Daily Debt: {filepath}")
        try:
            df = pd.read_excel(filepath, engine='openpyxl')
            for _, row in df.iterrows():
                self._process_nse_debt_row(row)
        except Exception as e:
            print(f"Error reading NSE Daily Debt: {e}")

    def _process_nse_debt_row(self, row: pd.Series):
        isin = str(row.get('ISIN_CODE', '')).strip()
        if not isin:
            return

        name = str(row.get('ISSUE_DESC', '')).strip()
        issue_type = str(row.get('ISSUE_TYPE', '')).strip().upper()

        bond_type = BondType.CORPORATE
        if issue_type in ['GS', 'SB', 'SDL']:
            bond_type = BondType.GOVERNMENT
        elif issue_type == 'TBILLS':
            bond_type = BondType.TBILL

        maturity_date = self._parse_date(row.get('MAT_DT'))
        coupon_rate = self._parse_decimal(row.get('COUPON_RATE'))

        # Ticker often missing in this file, use ISIN
        ticker = isin

        data = {
            "isin": isin,
            "ticker_symbol": ticker,
            "name": name,
            "asset_type": "BOND",
            "bond_type": bond_type,
            "maturity_date": maturity_date,
            "coupon_rate": coupon_rate,
            "exchange": "NSE"
        }
        self._create_asset(data)

    def process_bse_debt_bhavcopy(self, filepath: str):
        """Phase 3 Source 6: BSE Debt Bhavcopy (Zip)."""
        print(f"Processing BSE Debt Bhavcopy: {filepath}")
        try:
            with zipfile.ZipFile(filepath) as z:
                for filename in z.namelist():
                    if filename.lower().endswith(".csv"):
                        with z.open(filename) as f:
                            df = pd.read_csv(f)
                            self._process_bse_debt_csv(filename, df)
        except Exception as e:
            print(f"Error processing BSE Debt Zip: {e}")

    def _process_bse_debt_csv(self, filename: str, df: pd.DataFrame):
        # fgroup, icdm -> Corporate. wdm -> Govt usually
        is_gov = 'wdm' in filename.lower()

        for _, row in df.iterrows():
            # Column names vary slightly
            isin = row.get('ISIN No.') or row.get('ISIN')
            if not isin or pd.isna(isin):
                continue
            isin = str(isin).strip()

            ticker = (row.get('Security Code') or row.get('Security_cd') or
                      row.get('Scrip Code'))
            ticker = str(ticker).strip() if ticker else isin

            name = (row.get('sc_name') or row.get('Issuer Name') or
                    row.get('Security Description'))
            name = str(name).strip() if name else f"Bond {isin}"

            maturity_date = self._parse_date(
                row.get('Maturity Date') or row.get('MaturityDate')
            )
            coupon_rate = self._parse_decimal(
                row.get('COUP0N (%)') or
                row.get('Coupon (%)') or
                row.get('Coupon Rate (%)')
            )
            face_value = self._parse_decimal(
                row.get('Face Value') or row.get('FACE VALUE')
            )

            data = {
                "isin": isin,
                "ticker_symbol": ticker,
                "name": name,
                "asset_type": "BOND",
                "bond_type": BondType.GOVERNMENT if is_gov else BondType.CORPORATE,
                "maturity_date": maturity_date,
                "face_value": face_value,
                "coupon_rate": coupon_rate,
                "exchange": "BSE"
            }
            self._create_asset(data)

    # --- Phase 4: Indices ---
    def process_bse_index(self, filepath: str):
        """Phase 4 Source 7: BSE Index (CSV)."""
        print(f"Processing BSE Index: {filepath}")
        try:
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                ticker = str(row.get('IndexID', '')).strip()
                name = str(row.get('IndexName', '')).strip()

                if not ticker:
                    continue

                data = {
                    "isin": None, # Indices usually don't have ISINs in this file
                    "ticker_symbol": ticker,
                    "name": name,
                    "asset_type": "INDEX",
                    "exchange": "BSE"
                }
                self._create_asset(data)
        except Exception as e:
            print(f"Error reading BSE Index: {e}")

    # --- Phase 5: Fallback (ICICI) with Heuristics ---
    def process_icici_fallback(self, filepath: str):
        """Phase 5: ICICI Master (Zip/Txt) with Heuristics."""
        print(f"Processing Fallback (ICICI): {filepath}")
        try:
            with zipfile.ZipFile(filepath) as z:
                # Find the txt file
                txt_files = [
                    f for f in z.namelist()
                    if f.endswith(".txt") or f.endswith(".csv")
                ]
                for filename in txt_files:
                    with z.open(filename) as f:
                        # Assuming CSV/Txt format. ICICI usually comma or pipe?
                        # Code in cli.py used csv.DictReader, implying comma.
                        # But user might have different format now?
                        # Let's assume standard CSV for now or check extension.
                        df = pd.read_csv(f, on_bad_lines='skip')
                        for _, row in df.iterrows():
                             self._process_fallback_row(row)
        except Exception as e:
            print(f"Error processing Fallback Zip: {e}")

    def _process_fallback_row(self, row: pd.Series):
        # Standardize column names based on old cli.py config if possible
        # NSE: ExchangeCode, CompanyName, ISINCode, Series
        # BSE: ScripID, ScripName, ISINCode, Series

        # We try to detect which columns are present
        ticker = row.get('ExchangeCode') or row.get('ScripID')
        name = row.get('CompanyName') or row.get('ScripName')
        isin = row.get('ISINCode')
        series = row.get('Series', '')

        if not ticker or pd.isna(ticker):
            return
        ticker = str(ticker).strip()
        name = str(name).strip() if name else ""
        isin = str(isin).strip() if isin and not pd.isna(isin) else None
        series = str(series).strip().upper()

        # Apply Heuristic Classification
        asset_type, bond_type = self._classify_asset_heuristic(ticker, name, series)

        if not asset_type:
            # Default to Stock if heuristics fail?
            # The FR says "Pass 4: Default Classification...
            # classified as STOCK by default".
            asset_type = "STOCK"

        data = {
            "isin": isin,
            "ticker_symbol": ticker,
            "name": name,
            "asset_type": asset_type,
            "bond_type": bond_type,
            # Guess exchange
            "exchange": "NSE" if 'ExchangeCode' in row else "BSE"
        }
        self._create_asset(data)

    def _classify_asset_heuristic(
        self, ticker: str, name: str, series: str
    ) -> Tuple[Optional[str], Optional[BondType]]:
        """
        Refactored Heuristic Logic (FR 3.2).
        Returns (asset_type, bond_type).
        """
        name = name.upper()
        ticker = ticker.upper()

        # Pass 1: High-Confidence Stock Indicators
        stock_keywords = ["LIMITED RE", "RIGHTS ENT", "OFS", "PP", "WARRANTS"]
        if any(k in name for k in stock_keywords):
            return "STOCK", None

        # Pass 2: High-Confidence Bond Indicators
        # NSE Series N1-N9, NB-NZ, etc.
        if re.match(r"^[N][1-9A-Z]$", series): # Simplified check for N series
             return "BOND", BondType.CORPORATE

        if "NCD" in name or "DEBENTURE" in name:
             return "BOND", BondType.CORPORATE

        if "SGB" in ticker or series == "GB":
            return "BOND", BondType.SGB

        # Pass 3: Name-Based Heuristics for BSE Bonds
        # Rule A: Finance Bonds
        finance_keywords = ["FINANCE", "FINCORP", "FIN"]
        bond_indicators = ["SR-", "SR ", "%"]
        # Enhanced Rule A: Check for coupon pattern (e.g. 9.75)
        # and date pattern (e.g. 28AG20)
        has_coupon_pattern = bool(re.search(r"\b\d{1,2}\.\d{1,2}\b", name))
        # DDMMMYY
        has_complex_date = bool(re.search(r"\d{2}[A-Z]{2,3}\d{2}", name))

        is_finance = any(k in name for k in finance_keywords)
        has_bond_ind = any(k in name for k in bond_indicators)

        if is_finance and (has_bond_ind or has_coupon_pattern or has_complex_date):
            return "BOND", BondType.CORPORATE

        # Rule B: General Corporate Bonds
        months = [
            "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
        ]
        has_month = any(m in name for m in months)
        has_year = bool(re.search(r"20\d{2}", name)) # 20xx

        stock_exclusions = [
            "INDUSTRIES", "MANUFACTURING", "TECHNOLOGIES",
            "SYSTEMS", "PROJECTS"
        ]
        is_stock_excl = any(k in name for k in stock_exclusions)

        if (has_month or has_year) and not is_stock_excl:
            return "BOND", BondType.CORPORATE

        # Pass 4: Default (Handled by caller or return None)
        return None, None
