import logging
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Transaction, TransactionLink
from app.schemas.capital_gains import (
    CapitalGainsSummary,
    ForeignGainEntry,
    GainEntry,
    ITRPeriodValues,
    ITRRow,
    Schedule112AEntry,
)
from app.schemas.enums import BondType, TransactionType

logger = logging.getLogger(__name__)

# Tax Constants
HOLDING_PERIOD_EQUITY_LTCG = 365  # 12 months
HOLDING_PERIOD_GENERAL_LTCG_OLD = 1095  # 36 months (Pre July 2024)
HOLDING_PERIOD_GENERAL_LTCG_NEW = 730   # 24 months (Post July 2024)

DATE_2018_01_31 = date(2018, 1, 31)
DATE_2024_07_23 = date(2024, 7, 23)

DATE_2023_04_01 = date(2023, 4, 1)

class CapitalGainsService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_capital_gains(
        self,
        portfolio_id: Optional[str],
        fy_year: str, # e.g. "2025-26"
        slab_rate: float = 30.0 # Default to 30% if not provided
    ) -> CapitalGainsSummary:
        """
        Main entry point to calculate Capital Gains for a financial year.
        Separates domestic (INR) and foreign gains.
        """
        start_date, end_date = self._get_fy_dates(fy_year)

        # 1. Fetch ALL realized sell transactions for the FY
        # We need links to know which Buy lots were sold
        from sqlalchemy.orm import aliased

        from app.models.asset import Asset
        from app.models.transaction import Transaction

        SellTx = aliased(Transaction)
        BuyTx = aliased(Transaction)
        AssetModel = aliased(Asset)

        query = (
            select(TransactionLink)
            .join(TransactionLink.sell_transaction.of_type(SellTx))
            .join(TransactionLink.buy_transaction.of_type(BuyTx))
            .join(SellTx.asset.of_type(AssetModel))
            .where(
                SellTx.transaction_type == TransactionType.SELL,
                SellTx.transaction_date >= start_date,
                SellTx.transaction_date <= end_date
            )
        )

        if portfolio_id:
            query = query.where(SellTx.portfolio_id == portfolio_id)

        links = self.db.scalars(query).all()

        gains: List[GainEntry] = []
        foreign_gains: List[ForeignGainEntry] = []
        schedule_112a_entries: List[Schedule112AEntry] = []

        # Track totals (domestic only - foreign handled separately)
        total_stcg = Decimal(0)
        total_ltcg = Decimal(0)

        # Matrix Buckets (domestic only)
        matrix_data = defaultdict(lambda: {
            "upto_15_6": Decimal(0),
            "upto_15_9": Decimal(0),
            "upto_15_12": Decimal(0),
            "upto_15_3": Decimal(0),
            "upto_31_3": Decimal(0)
        })

        for link in links:
            sell_tx = link.sell_transaction
            buy_tx = link.buy_transaction
            asset = sell_tx.asset

            # Check if foreign asset
            is_foreign = asset.currency and asset.currency != "INR"

            if is_foreign:
                # Process as foreign gain (no INR conversion)
                foreign_entry = self._process_foreign_link(link, asset, sell_tx, buy_tx)
                foreign_gains.append(foreign_entry)
            else:
                # 2. Calculate Gain for this specific lot (domestic)
                entry, s112a_entry = self._process_single_link(
                    link, asset, sell_tx, buy_tx
                )
                gains.append(entry)

                if s112a_entry:
                    schedule_112a_entries.append(s112a_entry)

                # 3. Aggregate Totals
                if entry.gain_type == "STCG":
                    total_stcg += entry.gain
                else:
                    total_ltcg += entry.gain

                # 4. Bucketing for ITR Matrix
                sell_date = sell_tx.transaction_date.date()
                self._bucket_into_matrix(matrix_data, entry, sell_date, asset)

        # 5. Build Reports
        itr_matrix = self._build_itr_matrix(matrix_data)

        # 6. Estimate Tax (Simplistic estimation - domestic only)
        est_stcg_tax = Decimal(0)
        est_ltcg_tax = Decimal(0)
        
        # Slab rate as decimal
        slab_decimal = Decimal(str(slab_rate)) / Decimal(100)

        for g in gains:
            if g.gain <= 0:
                continue

            if g.gain_type == "STCG":
                if "Exempt" in g.tax_rate:
                    continue
                elif "STCG 20%" in g.tax_rate:
                    est_stcg_tax += g.gain * Decimal("0.20")
                elif "STCG 15%" in g.tax_rate:
                    est_stcg_tax += g.gain * Decimal("0.15")
                else:
                    # Slab Rate STCG
                    est_stcg_tax += g.gain * slab_decimal
            else: # LTCG
                if "Exempt" in g.tax_rate:
                    continue
                elif "LTCG 10%" in g.tax_rate:
                     # 1L Exemption not handled per stock, this is gross est
                     est_ltcg_tax += g.gain * Decimal("0.10")
                elif "LTCG 12.5%" in g.tax_rate:
                    est_ltcg_tax += g.gain * Decimal("0.125")
                elif "LTCG 20%" in g.tax_rate:
                    est_ltcg_tax += g.gain * Decimal("0.20")
                else:
                     # Fallback or Slab? Assuming 20% for unknown
                     est_ltcg_tax += g.gain * Decimal("0.20")

        return CapitalGainsSummary(
            financial_year=fy_year,
            total_stcg=total_stcg,
            total_ltcg=total_ltcg,
            estimated_stcg_tax=est_stcg_tax,
            estimated_ltcg_tax=est_ltcg_tax,
            itr_schedule_cg=itr_matrix,
            schedule_112a=schedule_112a_entries,
            gains=sorted(gains, key=lambda x: x.sell_date),
            foreign_gains=sorted(foreign_gains, key=lambda x: x.sell_date)
        )

    def _get_fy_dates(self, fy: str) -> Tuple[datetime, datetime]:
        # fy format "2025-26"
        start_year = int(fy.split("-")[0])
        start_date = datetime(start_year, 4, 1)
        end_date = datetime(start_year + 1, 3, 31, 23, 59, 59)
        return start_date, end_date

    def _process_foreign_link(
        self,
        link: TransactionLink,
        asset: Asset,
        sell_tx: Transaction,
        buy_tx: Transaction
    ) -> ForeignGainEntry:
        """
        Process a foreign asset gain entry.
        Values remain in native currency - no INR conversion.
        User/tax consultant must apply SBI TT Buy Rate (Rule 115) for ITR filing.
        """
        buy_date = buy_tx.transaction_date.date()
        sell_date = sell_tx.transaction_date.date()
        quantity = link.quantity

        buy_price = buy_tx.price_per_unit

        # --- ESPP Cost Basis Adjustment ---
        # For ESPP_PURCHASE, use FMV as cost basis, not discounted price.
        if (buy_tx.transaction_type in [
            TransactionType.ESPP_PURCHASE, TransactionType.RSU_VEST
        ] and buy_tx.details and "fmv" in buy_tx.details):
            buy_price = Decimal(str(buy_tx.details["fmv"]))

        sell_price = sell_tx.price_per_unit

        total_buy_value = buy_price * quantity
        total_sell_value = sell_price * quantity
        gain = total_sell_value - total_buy_value

        # Holding period for foreign assets: 24 months (unlisted)
        holding_days = (sell_date - buy_date).days
        is_ltcg = holding_days > 730  # 24 months

        # Country code: derive from asset.country or default from currency
        country_code = getattr(asset, 'country', None) or ""
        if not country_code and asset.currency:
            # Default country mapping for common currencies
            currency_country_map = {
                "USD": "US",
                "GBP": "GB",
                "EUR": "DE",  # Default to Germany for EUR
                "CAD": "CA",
                "AUD": "AU",
                "SGD": "SG",
                "JPY": "JP",
            }
            country_code = currency_country_map.get(asset.currency, "")

        return ForeignGainEntry(
            transaction_id=str(sell_tx.id),
            asset_ticker=asset.ticker_symbol,
            asset_name=asset.name,
            asset_type=asset.asset_type,
            currency=asset.currency or "USD",
            buy_date=buy_date,
            sell_date=sell_date,
            quantity=quantity,
            buy_price=buy_price,
            sell_price=sell_price,
            total_buy_value=total_buy_value,
            total_sell_value=total_sell_value,
            gain=gain,
            gain_type="LTCG" if is_ltcg else "STCG",
            holding_days=holding_days,
            country_code=country_code
        )

    def _process_single_link(
        self,
        link: TransactionLink,
        asset: Asset,
        sell_tx: Transaction,
        buy_tx: Transaction
    ) -> Tuple[GainEntry, Optional[Schedule112AEntry]]:

        buy_date = buy_tx.transaction_date.date()
        sell_date = sell_tx.transaction_date.date()
        quantity = link.quantity

        # --- Corporate Action Adjustment (Demerger) ---
        # Check if Buy Tx has Demerger adjustments
        # Logic: If Buy is Pre-Demerger, and we have demerger info, reduce Cost.
        # Note: This is complex. For now, we assume `buy_tx.price_per_unit`
        # is the raw price. We need to check if ANY demerger happened
        # for this asset between Buy and today.
        # Ideally, `crud_analytics` handles this logic of 'adjusted price'.
        # For v1.0, we will check `buy_tx.details` to see if it was explicitly updated?
        # No, the `HoldingDetailModal` computes it on fly.
        # We need a helper to get `adjusted_buy_price`.
        buy_price = buy_tx.price_per_unit

        # --- ESPP Cost Basis Adjustment ---
        # For ESPP_PURCHASE, use FMV as cost basis, not discounted price.
        # The perquisite benefit (FMV - discount price) is already taxed as income.
        if (buy_tx.transaction_type in [
            TransactionType.ESPP_PURCHASE, TransactionType.RSU_VEST
        ] and buy_tx.details and "fmv" in buy_tx.details):
            buy_price = Decimal(str(buy_tx.details["fmv"]))
            logger.debug(
                f"Using ESPP FMV {buy_price} as cost basis for {asset.ticker_symbol}"
            )

        # TODO: Implement demerger cost reduction lookup

        sell_price = sell_tx.price_per_unit

        cost_of_acquisition = buy_price * quantity
        full_value_consideration = sell_price * quantity

        # Classification
        asset_category = self._classify_asset_category(asset)
        holding_days = (sell_date - buy_date).days
        is_ltcg = self._is_ltcg(asset_category, holding_days, sell_date, buy_date) # Updated signature
        gain_type = "LTCG" if is_ltcg else "STCG"

        # Determine Tax Rate Label
        tax_rate_label = self._determine_tax_rate_label(
            gain_type, asset_category, sell_date, buy_date # Updated signature
        )

        # SGB Exemption Check (Redemption on Maturity)
        # SGB interest is taxable, but capital gains on redemption are tax free.
        if asset_category == "SGB" and asset.bond and asset.bond.maturity_date:
            if sell_date >= asset.bond.maturity_date:
                tax_rate_label = "Exempt (Maturity)"

        # SGB Premature Redemption Note
        note = None
        if asset_category == "SGB" and "Exempt" not in tax_rate_label:
            # 5 years = approx 1825 days
            if holding_days > 1825:
                 note = "Potential Exemption: Tax-free if redeemed with RBI (Premature)."

        # Grandfathering Logic
        fmv_2018 = None
        is_grandfathered = False
        if is_ltcg and asset_category == "EQUITY_LISTED" and buy_date < DATE_2018_01_31:
            is_grandfathered = True
            fmv_2018 = self._get_grandfathering_price(asset)
            if fmv_2018:
                # Formula: Cost = Max(Actual Cost, Min(FMV, SalePrice))
                # All per unit
                lower_of_fmv_sale = min(fmv_2018, sell_price)
                new_cost_per_unit = max(buy_price, lower_of_fmv_sale)
                cost_of_acquisition = new_cost_per_unit * quantity

        gain = full_value_consideration - cost_of_acquisition

        # Gain Entry
        entry = GainEntry(
            transaction_id=str(sell_tx.id),
            asset_ticker=asset.ticker_symbol,
            asset_name=asset.name,
            asset_type=asset.asset_type,
            buy_date=buy_date,
            sell_date=sell_date,
            quantity=quantity,
            buy_price=buy_price, # showing original buy price for reference
            sell_price=sell_price,
            total_buy_value=cost_of_acquisition,
            total_sell_value=full_value_consideration,
            gain=gain,
            gain_type=gain_type,
            holding_days=holding_days,
            tax_rate=tax_rate_label,
            is_grandfathered=is_grandfathered,
            is_hybrid_warning=self._is_hybrid_fund(asset),
            note=note
        )

        # Schedule 112A Entry (Only for Grandfathered Equity LTCG)
        s112a_entry = None
        if is_grandfathered and gain_type == "LTCG":
             s112a_entry = Schedule112AEntry(
                isin=asset.isin or "N/A",
                asset_name=asset.name,
                quantity=quantity,
                sale_price=sell_price,
                full_value_consideration=full_value_consideration,
                cost_of_acquisition_orig=buy_price * quantity,
                fmv_31jan2018=fmv_2018,
                total_fmv=(fmv_2018 * quantity) if fmv_2018 else None,
                cost_of_acquisition_final=cost_of_acquisition,
                expenditure=Decimal(0), # TODO: Add fees
                total_deductions=cost_of_acquisition,
                balance=gain,
                acquired_date=buy_date,
                transfer_date=sell_date
             )

        return entry, s112a_entry

    def _is_ltcg(
        self, category: str, days: int, sell_date: date, buy_date: date
    ) -> bool:
        """Determine if holding period qualifies for LTCG"""
        if category == "EQUITY_LISTED":
            return days > 365

        if category == "SGB":
            # Post July 2024 Rule: 12 months for Secondary Market
            if sell_date >= DATE_2024_07_23:
                return days > 365
            return days > 1095 # Old rule (36 months)

        if category == "DEBT":
            # Debt Fund Rules
            # 1. Invested ON/AFTER 1 Apr 2023 -> Always STCG (Sec 50AA)
            if buy_date >= DATE_2023_04_01:
                return False # Always Short Term regardless of holding
            
            # 2. Invested BEFORE 1 Apr 2023 -> Normal Debt Rules
            # Post July 2024 -> 24 months
            if sell_date >= DATE_2024_07_23:
                return days > 730
            # Pre July 2024 -> 36 months
            return days > 1095

        # General / Gold - 24 months post July 2024
        if category == "EQUITY_INTERNATIONAL":
            # Per User: Debt/Intl -> Any Period -> As per Slab Rate
            # This effectively means treated as Short Term for tax rates
            return False

        if sell_date >= DATE_2024_07_23:
            threshold = HOLDING_PERIOD_GENERAL_LTCG_NEW
        else:
            threshold = HOLDING_PERIOD_GENERAL_LTCG_OLD
        return days > threshold

    def _get_grandfathering_price(self, asset: Asset) -> Optional[Decimal]:
        """Get FMV as of Jan 31, 2018 from database"""
        return asset.fmv_2018

    def _classify_asset_category(self, asset: Asset) -> str:
        """
        Classifies asset into tax categories:
        - EQUITY_LISTED: Stocks, ETFs, Equity MFs (STT paid)
        - EQUITY_UNLISTED: Unlisted shares
        - EQUITY_INTERNATIONAL: Overseas ETFs/Funds (Taxed as Debt/Slab)
        - DEBT: Debt MFs, Corporate Bonds
        - SGB: Sovereign Gold Bonds
        - GOLD: Physical Gold, Gold ETFs (if treated as Debt/Gold)
        - FOREIGN: Foreign stocks
        """
        atype = str(asset.asset_type).upper()

        # 1. Foreign Assets
        if asset.currency != "INR":
            return "FOREIGN"

        # 2. Equity / ETF / Stock
        if atype in ["STOCK", "ETF"] or "MUTUAL" in atype:
            name_upper = str(asset.name).upper()
            sector_upper = str(asset.sector).upper() if asset.sector else ""
            ticker_upper = str(asset.ticker_symbol).upper()

            # A. Gold / Silver ETFs
            if "GOLD" in name_upper or "SILVER" in name_upper or "GOLD" in sector_upper or "SILVER" in sector_upper:
                return "GOLD"

            # B. Debt / Bond / Liquid ETFs
            debt_keywords = ["LIQUID", "GILT", "BOND", "DEBT", "GOVT", "TREASURY"]
            if any(k in name_upper for k in debt_keywords) or any(k in sector_upper for k in debt_keywords):
                return "DEBT"

            # C. International / Overseas ETFs (Treated as Debt for tax if > Apr 2023, else LTCG 20%/12.5%)
            # Examples: MAHKTECH, MON100, NASDAQ, HANG SENG, FANG, US EQUITY
            intl_keywords = ["NASDAQ", "HANG SENG", "US EQUITY", "Global", "WORLD", "OVERSEAS", "INTERNATIONAL", "MAHKTECH", "MON100", "FANG+"]
            if any(k in name_upper for k in intl_keywords) or any(k in sector_upper for k in intl_keywords):
                 return "EQUITY_INTERNATIONAL"

            # D. Explicit Mutual Fund Checks (if not caught above)
            if "MUTUAL" in atype:
                if "EQUITY" in sector_upper or "INDEX" in sector_upper or "ELSS" in sector_upper:
                    return "EQUITY_LISTED"
                return "DEBT"  # Default for MFs is Debt unless Equity sector

            # E. Default for Stock/ETF -> Equity Listed
            return "EQUITY_LISTED"

        # 3. Bonds
        if "BOND" in atype:
            if asset.bond and asset.bond.bond_type == BondType.SGB:
                return "SGB"
            return "DEBT" # Corporate/Govt Bonds

        if "GOLD" in atype: # Physical Gold placeholders
            return "GOLD"

        return "OTHER"

    def _is_hybrid_fund(self, asset: Asset) -> bool:
        """Check if asset is a Hybrid/Balanced fund requiring user verification"""
        if str(asset.asset_type).upper() != "MUTUAL FUND":
            return False
            
        keywords = ["HYBRID", "BALANCED", "DYNAMIC", "MULTI ASSET", "ARBITRAGE", "OTHER SCHEME"]
        sector = str(asset.sector).upper() if asset.sector else ""
        name = str(asset.name).upper()
        
        # Check both sector and name
        for k in keywords:
            if k in sector or k in name:
                return True
        return False

    def _determine_tax_rate_label(
        self, gain_type: str, category: str, sell_date: date, buy_date: date
    ) -> str:
        """
        Returns label like 'STCG 20%', 'LTCG 12.5%' based on rules.
        """
        is_post_july = sell_date >= DATE_2024_07_23

        if gain_type == "STCG":
            if category == "EQUITY_LISTED":
                return "STCG 20%" if is_post_july else "STCG 15%"
            
            # Debt Funds post Apr 2023 are purely slab rate (STCG)
            if category == "DEBT" and buy_date >= DATE_2023_04_01:
                return "STCG Slab"
            
            if category == "EQUITY_INTERNATIONAL":
                return "STCG Slab"

            # All other STCG is Slab
            return "STCG Slab"

        if gain_type == "LTCG":
            if category == "EQUITY_LISTED":
                return "LTCG 12.5%" if is_post_july else "LTCG 10%"

            if category in ["GOLD", "FOREIGN", "EQUITY_UNLISTED"]:
                # New Rule: 12.5% without indexation
                # Old Rule: 20% with indexation
                return "LTCG 12.5%" if is_post_july else "LTCG 20%"

            if category == "SGB":
                return "LTCG 12.5%" # Secondary market

            if category == "DEBT":
                # Only reaches here if Pre-Apr 2023 buy + >2/3yr hold
                # User Requirement: Taxed at 12.5% flat (if post-July 2024?)
                # Actually, user said: "For investments before April 1, 2023, gains after a 2-year hold are taxed at 12.5% without indexation"
                # This only applies if sold AFTER 23 July 2024.
                # If sold BEFORE 23 July 2024, old rule (20% with indexation) applies?
                # User Example used "sold in 2025".
                # We will handle "Post July 2024" as 12.5%
                if is_post_july:
                     return "LTCG 12.5%" 
                else:
                     return "LTCG 20%" # Old regime with indexation

        return "Unknown"

        current_val = matrix[row_key][period_key]
        matrix[row_key][period_key] = current_val + entry.gain

    def _bucket_into_matrix(
        self, matrix, entry: GainEntry, sell_date: date, asset: Asset
    ):
        if "Exempt" in entry.tax_rate:
            return

        # 1. Determine Period Column
        month = sell_date.month
        day = sell_date.day

        period_key = "upto_31_3"

        # FY starts in April.
        # Period 1: Apr 1 - Jun 15
        if (month == 4 or month == 5) or (month == 6 and day <= 15):
            period_key = "upto_15_6"
        # Period 2: Jun 16 - Sep 15
        elif (
            (month == 6 and day > 15)
            or (month == 7 or month == 8)
            or (month == 9 and day <= 15)
        ):
            period_key = "upto_15_9"
        # Period 3: Sep 16 - Dec 15
        elif (
            (month == 9 and day > 15)
            or (month == 10 or month == 11)
            or (month == 12 and day <= 15)
        ):
            period_key = "upto_15_12"
        # Period 4: Dec 16 - Mar 15
        elif (
            (month == 12 and day > 15)
            or (month == 1 or month == 2)
            or (month == 3 and day <= 15)
        ):
            period_key = "upto_15_3"
        # Period 5: Mar 16 - Mar 31
        else:
            period_key = "upto_31_3"

        # 2. Determine Row (Category)
        row_key = "LTCG Other" # Default

        # We invoke classification just to be sure, though we have tax_rate in entry now
        # But categorization for rows is strictly defined

        if entry.gain_type == "STCG":
             if "STCG 20%" in entry.tax_rate or "STCG 15%" in entry.tax_rate:
                 row_key = "STCG 20% (Equity)"
             else:
                 row_key = "STCG Slab (Debt/Gold)"
        else: # LTCG
             if "LTCG 12.5%" in entry.tax_rate or "LTCG 10%" in entry.tax_rate:
                 row_key = "LTCG 12.5% (Equity/Gold)"
             else:
                 row_key = "LTCG Other"

        current_val = matrix[row_key][period_key]
        matrix[row_key][period_key] = current_val + entry.gain

    def _build_itr_matrix(self, matrix_data) -> List[ITRRow]:
        rows = []
        # Define steady state order
        ordered_keys = [
            "STCG 20% (Equity)",
            "STCG Slab (Debt/Gold)",
            "LTCG 12.5% (Equity/Gold)",
            "LTCG Other"
        ]

        for key in ordered_keys:
            data = matrix_data.get(key, {
                "upto_15_6": Decimal(0),
                "upto_15_9": Decimal(0),
                "upto_15_12": Decimal(0),
                "upto_15_3": Decimal(0),
                "upto_31_3": Decimal(0)
            })

            rows.append(ITRRow(
                category_label=key,
                period_values=ITRPeriodValues(**data)
            ))

        return rows
