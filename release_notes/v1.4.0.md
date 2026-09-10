# Release Notes - ArthSaarthi v1.4.0 (Tax Readiness & Full Financial Picture)

**Release Date:** September 10, 2026  
**Tag:** `v1.4.0`  
**License:** Open Source / MIT  

---

## 🌟 Executive Summary

ArthSaarthi **v1.4.0 (Tax Readiness & Full Financial Picture)** transforms the platform into a comprehensive, privacy-first tax management and financial readiness hub. This milestone release equips individual investors and taxpayers with end-to-end income tracking, statutory Section 10(13A) HRA exemption math, Chapter VI-A deduction logging, dual tax regime (Old vs. New Section 115BAC) comparative analytics, and lot-level unrealized capital gains forecasting with Section 112A exemption pooling.

---

## 🚀 What's New in v1.4.0

### 1. Income Source & Entry Data Management (FR16.1 & FR16.2 / Issue #517)
- **Custom Income Sources:** Configure custom income categories across Salary, Freelance / Professional, Rental Income, Dividends, and Business Profits.
- **Income Transaction Ledger:** Log individual income events capturing gross amount, transaction date, payer/employer details, and Tax Deducted at Source (TDS).
- **Field-Level Encryption:** Sensitive financial amounts are stored using AES-256 (`EncryptedString`) on local desktop and mobile SQLite databases.

### 2. Salary Component Breakdown & Statutory Sec 10(13A) HRA Exemption (FR16.5 / Issue #532)
- **Granular Salary Logging:** Record Basic Salary, House Rent Allowance (HRA), Dearness Allowance (DA), Special / Flexible Allowances, Other Allowances, Other Benefits / Perquisites, Rent Paid, and Metro City classification.
- **Statutory HRA Exemption Engine:** Integrated `SalaryExemptionService` enforcing the statutory Indian Income Tax formula:
  $$\text{HRA Exemption} = \max\left(0,\; \min\left(\text{Actual HRA Received},\; \text{Rent Paid} - 10\% \times (\text{Basic} + \text{DA}),\; (50\% \text{ if Metro else } 40\%) \times (\text{Basic} + \text{DA})\right)\right)$$
- **Excel Benchmark Parity:** Verified 100% mathematical parity against cell `D101` in benchmark reference spreadsheet `local/TaxCalc_2027.xlsx`.
- **Live Exemption Preview:** Interactive drawer modal in `IncomeEntryModal.tsx` provides live, real-time calculation previews as salary components are entered.

### 3. Tax-Deductible Expense & Investment Logging under Chapter VI-A (FR16.3 / Issue #518)
- **Chapter VI-A Investments:** Track tax-saving investments eligible under Section 80C (PPF, ELSS, EPF, LIC, NPS), Section 80D (Medical Insurance), Section 80CCD(1B) (Additional NPS), and Section 80TTA / 80TTB (Savings & FD Interest).
- **Statutory Ceiling Meters:** Real-time visual progress bars displaying claimed contributions against statutory maximum limits (Section 80C ₹1,50,000; Section 80D ₹25,000; Section 80CCD(1B) ₹50,000; Section 80TTA ₹10,000; Section 80TTB ₹50,000).

### 4. Structured Tax Readiness Summary & Dual Regime Comparison (FR16.4 / Issue #519)
- **Versioned Statutory Tax Rules Registry:** Configurable tax rules engine supporting Assessment Years FY 2021-22 through FY 2026-27.
- **Old vs. New Tax Regime Comparative Analytics:** Automated evaluation of Old Tax Regime vs. New Tax Regime (Section 115BAC) tax liabilities, detailing net tax payable, Section 87A rebate eligibility, 4% Health & Education Cess, and highlighting recommended regime for maximum tax savings.
- **Export Pipelines:** Export consolidated tax summary reports to formatted CSV (`/api/v1/tax/summary/export/csv`) or publication-ready PDF documents (`/api/v1/tax/summary/export/pdf`).

### 5. Unrealized Capital Gains & Sec 112A Exemption Pooling (FR6.5 / Issue #516)
- **FIFO Lot-Level Unrealized Tax Projections:** Calculate unrealized Short-Term Capital Gains (STCG) and Long-Term Capital Gains (LTCG) across active equity and mutual fund holdings using live market feeds.
- **Grandfathering Support:** Automatic cost inflation adjustments and January 31, 2018 grandfathering valuation rules.
- **Section 112A Headroom Pooling:** Tracks remaining Section 112A ₹1,25,000 LTCG annual exemption headroom to assist in tax-loss harvesting and gain realization planning.

### 6. Intra-Head Capital Loss Set-Off Rules (FR6.5 Phase 3 / Issue #526)
- **Statutory Loss Set-Off Engine:** Enforces Income Tax Sections 70, 71, and 74 set-off rules (Short-Term Capital Losses set off against both STCG and LTCG; Long-Term Capital Losses set off strictly against LTCG).

---

## 🛡️ Security & Quality Enhancements

- **Dependabot Security Resolutions (Issue #546):**
  - Upgraded Python `cryptography` (50.0.1) resolving PKCS#7 Bleichenbacher oracle timing attack and path-building advisories.
  - Upgraded `pydantic-settings` (2.15.0) resolving symlink path traversal advisories.
  - Upgraded `soupsieve` (2.9.2) resolving ReDoS and memory exhaustion advisories.
  - Configured npm package overrides for `fast-uri`, `@xmldom/xmldom`, `browserslist`, `postcss-selector-parser`, `js-yaml`, `tar`, `@babel/core`, `nanoid`, and `ws`.
- **`SECRET_KEY` Persistence:** Local file persistence of `SECRET_KEY` to `secret.key` in app directory, preventing JWT session invalidation across application restarts.
- **Mobile SQLite Compatibility:** Dynamic string decoding decorator for Android Chaquopy embedded SQLite drivers.

---

## ✅ Automated Test & Quality Verification

- **Backend Pytest Suite (PostgreSQL & Redis):** 391 Passed / 0 Failed (3 expected skips)
- **Backend Integration Suite (Android / SQLite):** 391 Passed / 0 Failed (3 expected skips)
- **Frontend Jest Suite:** 201 Passed / 0 Failed (51/51 Test Suites clean)
- **Linters & Code Quality:** `ruff check` (0 warnings/errors) and `eslint` (0 warnings/errors)

---

## 📦 Downloads & Release Assets

| Target Platform | Package Format | Binary File Name |
| :--- | :--- | :--- |
| **Windows (x64)** | Setup Installer (.exe) | `ArthSaarthi-Windows-x64-Setup-v1.4.0.exe` |
| **macOS (Apple Silicon)** | Disk Image (.dmg) | `ArthSaarthi-macOS-arm64-v1.4.0.dmg` |
| **macOS (Intel)** | Disk Image (.dmg) | `ArthSaarthi-macOS-x64-v1.4.0.dmg` |
| **Linux (x64)** | AppImage | `ArthSaarthi-Linux-x64-v1.4.0.AppImage` |
| **Linux (x64)** | Debian Package | `ArthSaarthi-Linux-x64-v1.4.0.deb` |
| **Linux (ARM64)** | AppImage | `ArthSaarthi-Linux-arm64-v1.4.0.AppImage` |
| **Linux (ARM64)** | Debian Package | `ArthSaarthi-Linux-arm64-v1.4.0.deb` |
| **Android Mobile** | APK | `ArthSaarthi-Android-v1.4.0.apk` |
| **Docker Server** | Multi-Arch Image | `aashishbhanawat/arthsaarthi-backend:v1.4.0` / `arthsaarthi-frontend:v1.4.0` |
| **Source Code** | Archive (.zip) | `source-code-v1.4.0.zip` |

---

> [!IMPORTANT]
> **Statutory & Legal Notice Disclaimer:**  
> ArthSaarthi provides tax readiness calculations, regime recommendations, and capital gain estimates for **informational and self-assessment purposes only**. These calculations do **not** constitute official financial, legal, or tax advice. Users should consult a certified Chartered Accountant (CA) or tax professional before filing official tax returns.
