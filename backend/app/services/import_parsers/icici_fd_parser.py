# ruff: noqa: E501
import datetime
import logging
import re
from typing import Optional

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

from app.schemas.import_session import ParsedFixedDeposit
from app.services.import_parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class IciciFdParser(BaseParser):
    """
    Parser for ICICI Bank Statement (Fixed Deposits section).
    Extracts DEP.AMT. / DEPOSIT NO., Open Date, Principal, ROI%, MAT. DATE.
    """

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> list[ParsedFixedDeposit]:
        fixed_deposits: list[ParsedFixedDeposit] = []

        try:
            with pdfplumber.open(file_path, password=password or "") as pdf:
                in_fd_section = False

                # regex for DD-MM-YYYY or DD/MM/YYYY
                date_pattern = re.compile(r'\d{2}[/-]\d{2}[/-]\d{4}')

                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    # Look for the start of the FIXED DEPOSITS section
                    if "FIXED DEPOSITS" in text.upper():
                        in_fd_section = True

                    if not in_fd_section:
                        continue

                    lines = text.split("\n")
                    for line in lines:
                        dates = date_pattern.findall(line)
                        if len(dates) >= 2:
                            parts = line.split()
                            try:
                                date_indices = []
                                for i, p in enumerate(parts):
                                    if date_pattern.search(p):
                                        date_indices.append(i)

                                if len(date_indices) >= 2:
                                    open_date_idx = date_indices[0]
                                    mat_date_idx = date_indices[1]

                                    open_date_str = date_pattern.search(parts[open_date_idx]).group().replace('/', '-')
                                    start_date = datetime.datetime.strptime(open_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")

                                    mat_date_str = date_pattern.search(parts[mat_date_idx]).group().replace('/', '-')
                                    maturity_date = datetime.datetime.strptime(mat_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")

                                    # ICICI account numbers are usually the first token
                                    account_num = parts[0]
                                    # Sometimes masked or contains letters, let's just take it

                                    # Principal is usually right after open date
                                    principal_amount = 0.0
                                    for idx in range(open_date_idx + 1, mat_date_idx):
                                        try:
                                            val = float(parts[idx].replace(',', ''))
                                            if val > 15:  # unlikely to be an interest rate
                                                principal_amount = val
                                                break
                                        except ValueError:
                                            pass

                                    # ROI is typically a small number before maturity date
                                    interest_rate = 0.0
                                    for idx in range(open_date_idx + 1, len(parts)):
                                        try:
                                            # Strip percent sign if present
                                            clean_rate = parts[idx].replace('%', '').replace(',', '')
                                            val = float(clean_rate)
                                            if 0 < val < 15:
                                                interest_rate = val
                                                break
                                        except ValueError:
                                            pass

                                    # Maturity amount is right before maturity date
                                    maturity_amount = principal_amount  # Default if not found
                                    for idx in range(mat_date_idx - 1, open_date_idx, -1):
                                        try:
                                            # Strip commas
                                            val_str = parts[idx].replace(',', '')
                                            val = float(val_str)
                                            if val >= principal_amount:
                                                maturity_amount = val
                                                break
                                        except ValueError:
                                            pass

                                    if principal_amount > 0:
                                        interest_payout = "Cumulative"
                                        if abs(maturity_amount - principal_amount) < 1.0:
                                            interest_payout = "Payout"

                                        fd_entry = ParsedFixedDeposit(
                                            bank="ICICI",
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
                                logger.warning(f"Failed to parse ICICI FD row '{line}': {e}")
                                continue

            unique_fds = {}
            for fd in fixed_deposits:
                key = f"{fd.account_number}_{fd.start_date}_{fd.principal_amount}"
                unique_fds[key] = fd

            return list(unique_fds.values())

        except Exception as e:
            if isinstance(e, PDFPasswordIncorrect) or "PASSWORD_REQUIRED" in str(e) or str(e) == "":
                logger.error(f"Password required for PDF: {file_path}")
                raise ValueError("PASSWORD_REQUIRED")
            logger.error(f"Error parsing ICICI FD statement: {e}")
            raise ValueError(f"Failed to parse ICICI FD statement: {str(e)}")
