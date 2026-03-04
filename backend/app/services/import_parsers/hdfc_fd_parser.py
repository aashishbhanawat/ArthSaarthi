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


class HdfcFdParser(BaseParser):
    """
    Parser for HDFC Bank Statement (FD Details section).
    Extracts Account Number, Open/Last Renew Date, Maturity Date, Rate of Interest, Available Withdrawable, Maturity Amount.
    """

    def parse(
        self, file_path: str, password: Optional[str] = None
    ) -> list[ParsedFixedDeposit]:
        fixed_deposits: list[ParsedFixedDeposit] = []

        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                in_fd_section = False

                # regex for DD/MM/YYYY or DD-MM-YYYY
                date_pattern = re.compile(r'\d{2}[/-]\d{2}[/-]\d{4}')

                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    # Look for the start of the FD Details section
                    if "FD DETAILS" in text.upper() or "FIXED DEPOSIT" in text.upper():
                        in_fd_section = True

                    if "Details of TD Interest in current Financial Year" in text:
                        # Sometimes this is the next section, we should probably stop if we hit it but let's just
                        # skip this specific table as it has a different format.
                        # This section happens on Page 7. We want the section from Page 6.
                        in_fd_section = False

                    if not in_fd_section:
                        continue

                    lines = text.split("\n")

                    # HDFC FD table rows are often split across two lines
                    # e.g., Line 1: 50300049402823 INR 20,000.00   12/07/2025 6.25 0.00  41,585.82 YES
                    #       Line 2: 40,123.12          13/07/2026 39,078.82

                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        i += 1
                        if not line:
                            continue

                        # Look for potential account number start (14 digits)
                        parts1 = line.split()
                        if not parts1:
                            continue

                        # Check if first token is an account number candidate
                        clean_acct = "".join(c for c in parts1[0] if c.isdigit())
                        if len(clean_acct) >= 10:
                            # It's likely the start of an FD row
                            acc_num = clean_acct

                            row_text = line
                            # Check next line to see if it belongs to this row (usually starts with a number or date)
                            if i < len(lines):
                                next_line = lines[i].strip()
                                next_parts = next_line.split()
                                if next_parts and (date_pattern.match(next_parts[0]) or any(c.isdigit() for c in next_parts[0])):
                                    row_text += " " + next_line
                                    i += 1 # Consume next line

                            # Now process the combined row_text
                            try:
                                dates = date_pattern.findall(row_text)
                                if len(dates) >= 2:
                                    open_date_str = dates[0].replace('/', '-')
                                    start_date = datetime.datetime.strptime(open_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")

                                    mat_date_str = dates[-1].replace('/', '-')
                                    maturity_date = datetime.datetime.strptime(mat_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")

                                    # Extract all numeric values
                                    parts = row_text.split()
                                    numbers = []
                                    for p in parts:
                                        if date_pattern.match(p) or p == acc_num or "INR" in p.upper() or "YES" in p.upper() or "NO" in p.upper():
                                            continue
                                        clean_num = p.replace(",", "")
                                        try:
                                            numbers.append(float(clean_num))
                                        except ValueError:
                                            pass

                                    if not numbers:
                                        continue

                                    interest_rate = 0.0
                                    principal_amount = 0.0
                                    maturity_amount = 0.0

                                    rates = [n for n in numbers if 0 < n < 15]
                                    if rates:
                                        interest_rate = rates[0]

                                    amounts = [n for n in numbers if n >= 15]
                                    if len(amounts) >= 2:
                                        principal_amount = amounts[-1]
                                        maturity_amount = max(amounts)
                                    elif len(amounts) == 1:
                                        principal_amount = amounts[0]
                                        maturity_amount = amounts[0]

                                    if principal_amount > 0:
                                        interest_payout = "Cumulative"
                                        if abs(maturity_amount - principal_amount) < 1.0:
                                            interest_payout = "Payout"

                                        fd_entry = ParsedFixedDeposit(
                                            bank="HDFC",
                                            account_number=acc_num,
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
                                logger.warning(f"Failed to parse HDFC FD row '{row_text}': {e}")
                                continue

            # HDFC statements often duplicate FD rows in summary and detail. Let's deduplicate.
            unique_fds = {}
            for fd in fixed_deposits:
                key = f"{fd.account_number}_{fd.start_date}_{fd.principal_amount}"
                unique_fds[key] = fd

            return list(unique_fds.values())

        except Exception as e:
            if isinstance(e, PDFPasswordIncorrect) or "PASSWORD_REQUIRED" in str(e) or str(e) == "":
                logger.error(f"Password required for PDF: {file_path}")
                raise ValueError("PASSWORD_REQUIRED")
            logger.error(f"Error parsing HDFC FD statement: {e}")
            raise ValueError(f"Failed to parse HDFC FD statement: {str(e)}")
