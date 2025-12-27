# FR7.1.8 ICICI Securities MF Statement Parser

## Overview

Parser for **ICICI Securities Mutual Fund Account Statement** PDF files. ICICI Securities acts as a broker (AMFI ARN-0845) and provides consolidated statements covering MF transactions across multiple AMCs.

## Supported Format

| Attribute | Value |
|-----------|-------|
| **File Type** | PDF |
| **Source** | ICICI Securities (icici.com/icici-direct) |
| **Password Protected** | Yes (supported with password prompt) |

## Download Instructions

1. Login to ICICI Direct (icicidirect.com)
2. Navigate to **Reports** → **Mutual Fund** → **Account Statement**
3. Select date range and download PDF

## PDF Structure

### Header Information
- Statement Date and Period
- Customer Name, PAN, Address

### Transaction Block Format
```
AMC NAME Folio No: XXXXXXXXX
SCHEME NAME
Opening Balance As On DD-MMM-YYYY Units
DD-MMM-YYYY Transaction_No Transaction_Type NAV Units Amount TDS STT Net_Amount
Current Unit Balance As On DD-MMM-YYYY NAV Units Amount
```

### Column Mapping

| PDF Column | Parsed Field |
|-----------|--------------|
| Transaction Date | `transaction_date` (YYYY-MM-DD) |
| Transaction Type | `transaction_type` (BUY/SELL/DIVIDEND) |
| NAV | `price_per_unit` |
| Units | `quantity` |
| Scheme Name | `ticker_symbol` |

### Transaction Type Classification

| PDF Value | Internal Type |
|-----------|---------------|
| Purchase | BUY |
| SIP | BUY |
| Switch In | BUY |
| Systematic Investment | BUY |
| Redemption | SELL |
| Switch Out | SELL |
| Dividend | DIVIDEND |
| IDCW | DIVIDEND |

## Implementation Details

### Files
- Parser: `backend/app/services/import_parsers/icici_securities_parser.py`
- Factory: `backend/app/services/import_parsers/parser_factory.py`
- Frontend: `frontend/src/pages/Import/DataImportPage.tsx`

### Key Features
- Extracts scheme name from fund header lines
- Skips "Opening Balance" and "Current Unit Balance" rows
- Skips transaction number when parsing numeric columns
- Validates parsed values (units × NAV ≈ amount)
- Supports password-protected PDFs

### Number Extraction Order
The PDF contains columns in this order:
```
Transaction_No, NAV, Units, Gross_Amount, TDS, STT, Net_Amount
```

Parser skips index 0 (Transaction_No) and uses:
- `numbers[1]` = NAV (price)
- `numbers[2]` = Units (quantity)
- `numbers[3]` = Amount (for validation)

## Known Limitations

1. **Scheme Name as Ticker**: Uses fund name, not ISIN (ISIN not in PDF)
2. **Manual Mapping Required**: First-time imports require mapping schemes to assets
3. **Multiple Schemes Same Name**: Different plan variants may need separate mapping

## Testing

### Sample File
`MutualFundStatement (12).pdf` - Contains 4 pages with transactions across:
- Aditya Birla Sun Life funds
- DSP funds
- Franklin Templeton funds
- HSBC funds
- Nippon India funds

### Verification Steps
1. Select "ICICI Securities MF (PDF) - Mutual Funds" from dropdown
2. Upload the PDF file
3. Verify transactions are parsed with correct:
   - Dates (YYYY-MM-DD format)
   - Transaction types (BUY/SELL/DIVIDEND)
   - NAV values (small decimals, not transaction IDs)
   - Unit quantities
