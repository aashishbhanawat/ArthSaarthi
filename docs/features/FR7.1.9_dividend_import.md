# FR7.1.9 Dividend Statement Import

## Overview

Import dividend statements from broker platforms to automatically create DIVIDEND transactions.

## Supported Sources

| Source | Format | File Type |
|--------|--------|-----------|
| Zerodha | Excel (XLSX) | Equity dividends |
| ICICI DEMAT | PDF | Account statement with Corporate Benefits |

---

## Zerodha Dividend Statement

### Download Instructions
1. Login to console.zerodha.com
2. Navigate to **Reports** → **Tax P&L** → **Equity**
3. Download **Dividend Statement** for the financial year

### File Format
- **Header Rows:** 14 (Zerodha branding)
- **Columns:** Symbol, ISIN, Ex-Date, Quantity, Dividend Per Share, Net Dividend Amount

### Column Mapping

| XLSX Column | Internal Field |
|-------------|----------------|
| ISIN | `ticker_symbol` (ISIN:xxx format) |
| Ex-Date | `transaction_date` |
| Quantity | `quantity` |
| Dividend Per Share | `price_per_unit` |

---

## ICICI DEMAT Statement

### Download Instructions
1. Login to icicidirect.com
2. Navigate to **Portfolio** → **Demat Account** → **Account Statement**
3. Download PDF for the period containing dividends

### File Format
- **Format:** PDF
- **Section:** "Corporate Benefits for record date/payment date..."
- Contains dividends, bonuses, and other corporate actions

### Column Mapping

| PDF Column | Internal Field |
|------------|----------------|
| ISIN | `ticker_symbol` (ISIN:xxx format) |
| Record Date | `transaction_date` |
| No. of Units on which entitled | `quantity` |
| Value of benefit | Calculated as `quantity × price_per_unit` |

### Parsing Notes
- Only rows with "Dividend" in Nature column are parsed
- Expected/future dividends section is skipped
- Dividend per share is calculated from value/units

---

## Implementation Files

### Backend
- `backend/app/services/import_parsers/zerodha_dividend_parser.py`
- `backend/app/services/import_parsers/icici_demat_dividend_parser.py`
- `backend/app/services/import_parsers/parser_factory.py`
- `backend/app/api/v1/endpoints/import_sessions.py`

### Frontend
- `frontend/src/pages/Import/DataImportPage.tsx`

---

## Transaction Details

| Field | Value |
|-------|-------|
| `transaction_type` | DIVIDEND |
| `ticker_symbol` | ISIN:xxx format |
| `quantity` | Units entitled |
| `price_per_unit` | Dividend per share |
| `fees` | 0.0 |

---

## Testing

### Zerodha Dividend
- Sample: `dividends-CT0601-2025_2026.xlsx`
- Expected: JSWINFRA (119.2), MAHLOG (500), EPL (437.5)...

### ICICI DEMAT Dividend
- Sample: `dividend_statement_12_22_2025 (10).pdf`
- Expected: ORIENT PAPER (4), SREE SAKTHI PAPER (360), SOUTH INDIA (330)
