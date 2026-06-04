import logging
import re
import sys

# Add app to path
sys.path.insert(0, "/app")

from app.db.session import SessionLocal
from app.models.asset import Asset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_misclassified_bonds():
    db = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        # Find all assets currently classified as BOND
        bond_assets = (
            db.query(Asset)
            .options(joinedload(Asset.bond))
            .filter(Asset.asset_type == "BOND")
            .all()
        )
        logger.info(f"Found {len(bond_assets)} assets classified as BOND.")

        months = [
            "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
        ]
        fixed_count = 0

        for asset in bond_assets:
            name = asset.name.upper()
            ticker = asset.ticker_symbol.upper()

            # 1. Government / Sovereign Bonds
            is_gov = any(k in name for k in [
                "GSEC", "GOI", "SDL", "STRIP", "T-BILL", "TBILL",
                "TREASURY BILL"
            ]) or "SGB" in ticker or "SOVEREIGN GOLD" in name

            # 2. Corporate Bond Keywords
            is_corp_kw = any(k in name for k in [
                "NCD", "DEBENTURE", "PERP", "ZEROCOUP", "SUB DEBT",
                "TIER I", "TIER II", "UPPER TIER", "INFRA BOND"
            ])

            # 3. Bond Structural Indicators
            has_fv = bool(re.search(
                r"\bFV\s*\d+\s*(L|LAC|CR|K|00)\b", name
            ))
            has_complex_date = bool(re.search(
                r"\d{2}[A-Z]{2,3}\d{2}", name
            ))
            has_series = bool(re.search(
                r"\b(SR|SERIES|OP|OPT)\s*[-]?\s*[IVX\d]+\b", name
            ))
            is_tax_free = "TAX FREE" in name

            # 4. Contextual Heuristics
            is_finance = any(
                k in name for k in ["FINANCE", "FINCORP", "FIN"]
            )
            has_bond_ind = any(k in name for k in ["SR-", "SR ", "%"])
            has_coupon_pattern = bool(re.search(
                r"\b\d{1,2}\.\d{1,2}\b", name
            ))

            # Old month match vs new month match
            matched_old_month = any(m in name for m in months)
            matched_new_month = bool(re.search(
                r"(\b|\d)(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
                r"(\b|\d)",
                name
            ))
            has_year = bool(re.search(r"20\d{2}", name))

            # Determine if it qualifies as a strong bond indicator or legitimate bond
            is_legit_bond = (
                is_gov or is_corp_kw or has_fv or has_complex_date or
                has_series or is_tax_free or
                (is_finance and (
                    has_bond_ind or has_coupon_pattern
                    or has_complex_date
                )) or has_year or matched_new_month
            )

            # It's a false positive if it was classified as BOND under old rules
            # (matched_old_month) but does not match under new rules.
            is_false_positive = (
                not is_legit_bond and matched_old_month
                and not matched_new_month
            )

            if is_false_positive:
                logger.info(
                    f"Correcting misclassified asset: {asset.ticker_symbol} "
                    f"({asset.name}) from BOND to STOCK."
                )

                # Change asset type
                asset.asset_type = "STOCK"

                # Delete associated bond record if exists
                associated_bond = asset.bond
                if associated_bond:
                    logger.info(
                        f"  Deleting linked Bond record with ID "
                        f"{associated_bond.id}."
                    )
                    db.delete(associated_bond)

                fixed_count += 1

        if fixed_count > 0:
            db.commit()
            logger.info(
                f"Successfully corrected {fixed_count} misclassified assets."
            )
        else:
            logger.info("No misclassified assets found in the database.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error executing correction script: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_misclassified_bonds()
