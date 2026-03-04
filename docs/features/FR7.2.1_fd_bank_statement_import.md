# Feature Plan: FD Bank Statement Import (FR7.2.1)

**Feature ID:** FR7.2.1  
**Title:** Fixed Deposit Import from Bank Statements (HDFC, ICICI, SBI)  
**Priority:** P2  
**Parent FR:** FR7 (Automated Data Import)  
**User Story:** As a user, I want to import my Fixed Deposit details from combined bank statements (PDFs) so that I don't have to manually enter each FD.

---

## 1. Objective

Enable users to upload password-protected combined bank statement PDFs from HDFC, ICICI, and SBI banks, automatically extract Fixed Deposit details (account number, principal, interest rate, start/maturity dates), and present them on an editable review page before committing to the portfolio.

---

## 2. Sources

### 2.1 HDFC Bank Combined Statement

| Attribute | Value |
|-----------|-------|
| Source | HDFC NetBanking → Combined Statement |
| Format | PDF (password-protected with Customer ID) |
| Section | "FD Details :- FOR CURRENT FINANCIAL YEAR" |

**Field Mapping:**

| PDF Field | FD Model Field |
|-----------|----------------|
| FD Number | `account_number` |
| Open/Last Renew Date | `start_date` |
| Maturity Date | `maturity_date` |
| Rate of Interest | `interest_rate` |
| Maturity Amount | `maturity_amount` (for payout detection) |
| Available Withdrawable | `principal_amount` |

### 2.2 ICICI Bank Combined Statement

| Attribute | Value |
|-----------|-------|
| Source | ICICI NetBanking → Combined Statement |
| Format | PDF (password-protected) |
| Section | "FIXED DEPOSITS - INR" |

**Field Mapping:**

| PDF Field | FD Model Field |
|-----------|----------------|
| DEP.AMT. / DEPOSIT NO. | `account_number` |
| Open Date | `start_date` |
| Principal | `principal_amount` |
| ROI% | `interest_rate` |
| MAT. DATE | `maturity_date` |

### 2.3 SBI Combined Statement

| Attribute | Value |
|-----------|-------|
| Source | SBI → Combined Statement / eStatement |
| Format | PDF (password-protected) |
| Section | "FIXED DEPOSITS" → "TDR AND STDR ACCOUNTS" |

**Field Mapping:**

| PDF Field | FD Model Field |
|-----------|----------------|
| Account Number | `account_number` (first 7 chars masked with X) |
| Account Open Date | `start_date` (⚠️ original date for auto-renewed FDs; user must correct) |
| Principal Amount | `principal_amount` |
| ROI | `interest_rate` |
| Maturity Amount | `maturity_amount` (for payout detection) |
| Maturity Date | `maturity_date` |

---

## 3. Design Decisions

### 3.1 Separate FD Import Flow

FDs are standalone entities (not asset+transaction based). The existing import pipeline (`ParsedTransaction` → asset resolution → transaction commit) does not apply. A **parallel FD-specific import flow** is required:

1. Upload & Parse → `POST /import-sessions/fd`
2. Preview (editable) → `POST /import-sessions/{id}/fd-preview`
3. Commit → `POST /import-sessions/{id}/fd-commit`

The existing `ImportSession` model is reused for session tracking.

### 3.2 Payout Detection

If `maturity_amount == principal_amount`, the FD is a **Payout** type. Otherwise it is **Cumulative**.

### 3.3 Default Compounding Frequency

Default `compounding_frequency` is **Quarterly** for both Payout and Cumulative FDs. Users can correct this on the editable preview page before committing.

### 3.4 Auto-Generated Name

Each imported FD is named `"{Bank} FD - {account_number}"`.

---

## 4. Implementation

### 4.1 Backend

**New Files:**
- `backend/app/services/import_parsers/hdfc_fd_parser.py`
- `backend/app/services/import_parsers/icici_fd_parser.py`
- `backend/app/services/import_parsers/sbi_fd_parser.py`

**Modified Files:**
- `backend/app/services/import_parsers/parser_factory.py` — Register 3 new parsers
- `backend/app/schemas/import_session.py` — Add `ParsedFixedDeposit`, `FDImportPreview`, `FDImportCommit`
- `backend/app/schemas/__init__.py` — Export new schemas
- `backend/app/api/v1/endpoints/import_sessions.py` — Add 3 FD import endpoints

**Parser Pattern:** All parsers follow the existing `IciciDematDividendParser` pattern — `parse(file_path, password)` using `pdfplumber`. They return `list[ParsedFixedDeposit]`.

### 4.2 Frontend

**New Files:**
- `frontend/src/pages/Import/FDImportPreviewPage.tsx` — Editable preview table

**Modified Files:**
- `frontend/src/pages/Import/DataImportPage.tsx` — Add 3 FD source types to dropdown
- `frontend/src/types/import.ts` — Add FD import interfaces
- `frontend/src/services/importApi.ts` — Add FD API functions
- `frontend/src/hooks/useImport.ts` — Add FD hooks
- `frontend/src/App.tsx` — Add FD preview route

### 4.3 FD Preview Page

The preview page renders a table with inline-editable fields:
- Bank, Account Number, Principal, Interest Rate, Start Date, Maturity Date
- **Editable:** `start_date` (critical for SBI auto-renewed FDs), `compounding_frequency`, `interest_payout`.
- Checkbox selection for which FDs to commit.
- **Duplicate & Renewal Detection:** Matches FDs by `account_number` in the same portfolio.
  - If `account_number` AND `start_date` match an existing FD, it is flagged as a **Duplicate** (to skip).
  - If `account_number` matches but `start_date` differs, it is treated as a **New FD (Renewal)**. This ensures the old matured FD remains in the database to preserve historical portfolio value calculations.

---

## 5. Acceptance Criteria

- [x] User can upload HDFC combined statement PDF and extract FD details
- [x] User can upload ICICI combined statement PDF and extract FD details
- [x] User can upload SBI combined statement PDF and extract FD details
- [x] Password-protected PDFs are handled (password prompt shown)
- [x] Preview page displays parsed FDs with correct field mapping
- [x] All fields are editable on preview page before commit
- [x] Start date is editable (for SBI auto-renew correction)
- [x] Compounding frequency defaults to Quarterly, editable
- [x] Payout/Cumulative auto-detected from maturity vs principal amount
- [x] Duplicate FDs detected by `account_number` AND `start_date` (perfect match). Renewals (same `account_number`, diff `start_date`) treated as new FDs to preserve history.
- [x] Committed FDs appear correctly in portfolio

---

## 6. Testing

### 6.1 Unit Tests

- `test_hdfc_fd_parser.py` — Test with synthetic text matching HDFC FD section format
- `test_icici_fd_parser.py` — Test with synthetic text matching ICICI FD section format
- `test_sbi_fd_parser.py` — Test with synthetic text matching SBI TDR/STDR table format

### 6.2 Manual Testing

Upload each sample bank statement PDF through the UI, verify parsed FDs on preview page, correct any fields, commit, and verify FDs appear in portfolio.

---

## 7. Notes

- Combined bank statements are large PDFs (400KB-500KB); parsing may take 20-30 seconds
- Account numbers in SBI statements are partially masked (first 7 chars are X)
- SBI `Account Open Date` reflects the original FD date, not renewal date — users must manually correct for auto-renewed FDs
