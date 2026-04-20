# ruff: noqa: E501
import datetime
import logging
from typing import Optional

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

from app.schemas.import_session import ParsedFixedDeposit
from app.services.import_parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class SbiFdParser(BaseParser):
    """
    Parser for SBI Bank Statement (Fixed Deposits section).
    Extracts Account Number, Open Date, Principal Amount, ROI%, Maturity Amount, Maturity Date.
    Row format example:
    TERM DEPOSIT XXXXXXX3276 07-12-15 26613.36 P 6.25 0.00 258.74 28316.00 07-12-26 Yes
    """

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> list[ParsedFixedDeposit]:
        fixed_deposits: list[ParsedFixedDeposit] = []

        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                in_fd_section = False

                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    # Look for the start of the FIXED DEPOSITS section
                    if "FIXED DEPOSITS" in text or "TDR AND STDR ACCOUNTS" in text:
                        in_fd_section = True
                    elif "OTHER INVESTMENTS" in text or "TRANSACTION DETAILS" in text:
                        in_fd_section = False

                    if not in_fd_section:
                        continue

                    lines = text.split("\n")
                    for line in lines:
                        parts = line.split()

                        # Expected minimum parts for a valid row:
                        # e.g.: TERM DEPOSIT XXXXXXX3276 07-12-15 26613.36 P 6.25 0.00 258.74 28316.00 07-12-26 Yes
                        if len(parts) >= 11 and ("TERM" in parts or "DEPOSIT" in parts or "SPECIAL" in parts or "STDR" in parts or "TDR" in parts):
                            try:
                                # Look for date pattern DD-MM-YY to anchor our search
                                date_indices = [i for i, part in enumerate(parts) if len(part) == 8 and part.count('-') == 2]

                                if len(date_indices) >= 2:
                                    open_date_idx = date_indices[0]
                                    mat_date_idx = date_indices[1]

                                    # Account number is usually right before open date
                                    account_num = parts[open_date_idx - 1]

                                    # Parse dates (DD-MM-YY to YYYY-MM-DD)
                                    open_date_str = parts[open_date_idx]
                                    start_date = datetime.datetime.strptime(open_date_str, "%d-%m-%y").strftime("%Y-%m-%d")

                                    mat_date_str = parts[mat_date_idx]
                                    maturity_date = datetime.datetime.strptime(mat_date_str, "%d-%m-%y").strftime("%Y-%m-%d")

                                    # Principal is right after open date
                                    principal_str = parts[open_date_idx + 1].replace(',', '')
                                    principal_amount = float(principal_str)

                                    # Maturity amount is right before maturity date
                                    mat_amount_str = parts[mat_date_idx - 1].replace(',', '')
                                    maturity_amount = float(mat_amount_str)

                                    # ROI is typically a few columns after principal (after Holding status like 'P')
                                    # Look for the first float-like value
                                    interest_rate = 0.0
                                    for p in parts[open_date_idx + 2 : mat_date_idx - 1]:
                                        try:
                                            interest_rate = float(p.replace(',', ''))
                                            # ROI shouldn't be zero if it's an FD, usually between 2 and 12
                                            if interest_rate > 0 and interest_rate < 15:
                                                break
                                        except ValueError:
                                            continue

                                    # Determine payout type
                                    # If maturity amount == principal amount, it's typically a Payout FD (interest paid out periodically)
                                    # Otherwise, it's Cumulative
                                    interest_payout = "Cumulative"
                                    if abs(maturity_amount - principal_amount) < 1.0:
                                        interest_payout = "Payout"

                                    fd_entry = ParsedFixedDeposit(
                                        bank="SBI",
                                        account_number=account_num,
                                        principal_amount=principal_amount,
                                        interest_rate=interest_rate,
                                        start_date=start_date,
                                        maturity_date=maturity_date,
                                        maturity_amount=maturity_amount,
                                        interest_payout=interest_payout,
                                        compounding_frequency="Quarterly"
                                    )
                                    fixed_deposits.append(fd_entry)
                            except Exception as e:
                                logger.warning(f"Failed to parse SBI FD row '{line}': {e}")
                                continue

            return fixed_deposits

        except Exception as e:
            if isinstance(e, PDFPasswordIncorrect) or "PASSWORD_REQUIRED" in str(e) or str(e) == "":
                logger.error(f"Password required for PDF: {file_path}")
                raise ValueError("PASSWORD_REQUIRED")
            logger.error(f"Error parsing SBI FD statement: {e}")
            raise ValueError(f"Failed to parse SBI FD statement: {str(e)}")
