# Feature Plan: Automated Data Import (FR7)

## 1. Objective

To enable users to efficiently import their financial transaction and holding data from various external sources, specifically broker statements (Zerodha, ICICI) and Mutual Fund (MF) Consolidated Account Statements (CAS), into the Personal Portfolio Management System. The system will provide robust parsing, intelligent column mapping, and user-controlled reconciliation of duplicate or conflicting entries.

## 2. Functional Requirements

### 2.1. File Upload & Initial Processing

*   **FR7.1.1 - File Input:** Provide a user-friendly interface (e.g., drag-and-drop area, file selection button) for uploading single or multiple financial statement files.
*   **FR7.1.2 - Supported Formats:**
    *   **Tabular Data:** Support CSV, and potentially Excel (XLSX) for broker statements.
    *   **Structured Documents:** Support PDF (for MF CAS and some broker statements) and HTML (for some broker web reports).
*   **FR7.1.3 - Automatic Format Detection:** The system will attempt to automatically detect the file type and content structure upon upload.
*   **FR7.1.4 - Initial Data Extraction:**
    *   For tabular files: Perform an initial parse to identify potential headers, delimiters, and extract raw rows.
    *   For structured documents (PDF/HTML): Apply predefined parsing rules/templates for known formats (e.g., Zerodha, ICICI, MF CAS) to extract relevant data points.

### 2.2. Interactive Column/Field Mapping (for Tabular Data - CSV, etc.)

*   **FR7.2.1 - Trigger Mapping Interface:** If the system cannot confidently map columns to internal fields (e.g., for generic CSVs or unknown formats), or if parsing is ambiguous, present an interactive mapping interface.
*   **FR7.2.2 - Data Preview:** Display a preview of the first few rows of the parsed data, showing detected columns (e.g., "Column A", "Column B", or auto-detected headers).
*   **FR7.2.3 - Manual Column Assignment:** For each detected column, provide a dropdown or input field allowing the user to explicitly map it to a predefined internal data field (e.g., "Transaction Date", "Ticker Symbol", "Quantity", "Price", "Transaction Type", "ISIN", "Exchange", "Amount", "Brokerage", "Tax").
*   **FR7.2.4 - Smart Mapping Suggestions:**
    *   **Header-based Matching:** Automatically suggest mappings based on fuzzy matching of column headers (e.g., "Txn Date" -> "Transaction Date", "Scrip" -> "Ticker Symbol", "Amt" -> "Amount").
    *   **Content-based Inference:** Analyze data types and patterns within columns to infer and suggest appropriate mappings (e.g., columns with date formats suggest "Transaction Date"; columns with numbers and decimals suggest "Quantity" or "Price").
*   **FR7.2.5 - Delimiter & Encoding Options:** Allow users to manually select the correct delimiter (comma, semicolon, tab) and character encoding (UTF-8, ISO-8859-1) if auto-detection fails.
*   **FR7.2.6 - "Skip Column" Option:** Allow users to ignore irrelevant columns from the import.
*   **FR7.2.7 - Save Mapping Template (Future):** Provide an option for users to save their custom column mappings as a reusable template for future imports from the same source.

### 2.3. Data Extraction for Structured Documents (PDF/HTML)

*   **FR7.3.1 - Predefined Parsers:** Implement specific parsers/templates for common Indian broker statements (Zerodha, ICICI) and MF CAS PDF files. These parsers will extract data automatically based on their known structures.
*   **FR7.3.2 - OCR Integration (Future):** Explore and integrate Optical Character Recognition (OCR) for scanned documents or less structured PDFs (future enhancement).
*   **FR7.3.3 - Data Normalization:** Normalize extracted data (e.g., date formats, currency symbols, transaction types) to fit the system's internal data models.

### 2.4. Transaction & Holding Reconciliation

*   **FR7.4.1 - Duplicate Detection:** For each incoming transaction, generate a unique identifier based on a combination of key attributes (e.g., Asset Ticker/ISIN, Transaction Date, Transaction Type, Quantity, Price, Portfolio ID).
*   **FR7.4.2 - Conflict Detection:** Identify transactions that are similar to existing records but have minor differences (e.g., same core details but different brokerage or tax amounts).
*   **FR7.4.3 - User-Controlled Resolution:** Present potential duplicates and conflicts to the user for review and decision-making. Provide options for each flagged entry:
    *   **"Ignore (Skip)":** Do not import this specific transaction.
    *   **"Update Existing":** Overwrite the existing database record with the new data from the import file.
    *   **"Add Anyway":** Import the transaction as a new, separate entry.
    *   **"Merge (Future)":** Allow merging of specific data points for complex scenarios.
*   **FR7.4.4 - Batch Actions:** Provide options to apply a chosen resolution (e.g., "Ignore All Duplicates") to multiple flagged entries simultaneously.

### 2.5. User Review & Confirmation

*   **FR7.5.1 - Pre-Import Summary:** After parsing and mapping (and reconciliation of duplicates/conflicts), display a comprehensive summary of all transactions ready for import.
*   **FR7.5.2 - Highlight Changes:** Clearly indicate which transactions are new, which are updates, and which have been skipped.
*   **FR7.5.3 - Final Confirmation:** Require explicit user confirmation before committing the imported data to the database.

### 2.6. Error Handling & Reporting

*   **FR7.6.1 - Detailed Error Messages:** Provide clear, actionable error messages for parsing failures, validation errors, or import issues, indicating the specific line number or data point causing the problem.
*   **FR7.6.2 - Partial Import:** Allow successful transactions to be imported even if some entries fail, rather than failing the entire import.
*   **FR7.6.3 - Import Log/History:** Maintain a log of past import operations, including status (success/failure), number of records imported, skipped, or updated, and any errors encountered.

## 3. Non-Functional Requirements

*   **NFR7.1 - Security:**
    *   **Data Privacy:** Ensure uploaded financial data is handled securely, encrypted at rest and in transit.
    *   **Access Control:** Only authenticated and authorized users can upload and manage their own data.
    *   **Input Validation:** Rigorous validation of all parsed data to prevent injection attacks or malformed data.
*   **NFR7.2 - Performance:**
    *   Efficient parsing and processing of large files (e.g., thousands of transactions).
    *   Responsive UI during mapping and review stages.
    *   Optimized database operations for bulk inserts/updates.
*   **NFR7.3 - Usability:**
    *   Intuitive and guided import wizard/flow.
    *   Clear visual feedback on import progress, success, and errors.
    *   Easy-to-understand options for conflict resolution.
*   **NFR7.4 - Scalability:**
    *   The parsing and processing logic should be designed to handle increasing volumes of data and concurrent users.
    *   Consider background processing for very large files to avoid UI blocking.
*   **NFR7.5 - Maintainability:**
    *   Modular design for parsers, allowing easy addition of new broker formats.
    *   Well-documented code and clear separation of concerns.
*   **NFR7.6 - Data Integrity:**
    *   Ensure atomicity of import operations (all or nothing for a confirmed batch).
    *   Accurate mapping and transformation of external data to internal models.

## 4. High-Level Technical Design

### 4.1. Backend

*   **API Endpoints:**
    *   `POST /api/v1/import/upload`: For file upload.
    *   `GET /api/v1/import/preview`: To get a preview of parsed data (for mapping/review).
    *   `POST /api/v1/import/confirm`: To commit data to the database after user confirmation.
*   **Core Logic:**
    *   **File Upload Handler:** Receives files, stores them temporarily.
    *   **Parser Orchestrator:** Determines which parser to use based on file type/content.
    *   **Data Validation & Transformation:** Validates parsed data against schemas, transforms to internal models.
    *   **Duplicate/Conflict Detection Engine:** Implements the logic for identifying duplicates and conflicts.
    *   **Database Interaction:** Uses existing CRUD operations for `Transaction` and `Asset` models. May use temporary staging tables for large imports before final commit.
*   **Parsers (`app/services/import_parsers/` - New Directory):**
    *   `base_parser.py`: Abstract base class for parsers.
    *   `csv_parser.py`: Generic CSV parser with column mapping capabilities.
    *   `zerodha_parser.py`: Specific parser for Zerodha statements (CSV/PDF).
    *   `icici_parser.py`: Specific parser for ICICI statements (CSV/PDF/HTML).
    *   `mf_cas_parser.py`: Specific parser for MF CAS (PDF).
*   **Data Models:**
    *   Existing `app/models/transaction.py`, `app/models/asset.py`, `app/models/portfolio.py` will be used.
    *   Potentially new Pydantic schemas in `app/schemas/import.py` for intermediate parsed data structures.

### 4.2. Frontend

*   **File Upload Component:** React component for file selection/drag-and-drop.
*   **Column Mapping Component:** React component to display data preview and allow interactive column mapping (for CSVs).
*   **Review & Conflict Resolution Component:** React component to display parsed transactions, highlight duplicates/conflicts, and provide resolution options.
*   **Progress/Status Indicators:** Visual feedback during upload, parsing, and import.
*   **Error Display:** Clear display of any errors during the process.

## 5. User Flow Example: Uploading a Zerodha CSV

1.  **User Action:** User navigates to "Data Import" page.
2.  **System Action:** Displays file upload interface.
3.  **User Action:** User drags and drops a Zerodha CSV statement.
4.  **System Action (Backend):**
    *   Receives file.
    *   Identifies it as a Zerodha CSV.
    *   Uses `zerodha_parser.py` to extract transactions (date, ticker, type, quantity, price, etc.).
    *   Validates extracted data.
    *   Compares extracted transactions against existing database records for duplicates/conflicts.
    *   Sends parsed data, along with duplicate/conflict flags, to the frontend.
5.  **System Action (Frontend):**
    *   Displays a "Review Import" screen.
    *   Shows a table of all transactions from the file.
    *   Highlights potential duplicates/conflicts with clear indicators.
    *   Provides resolution options for each flagged entry (Ignore, Update Existing, Add Anyway).
6.  **User Action:** User reviews the transactions, resolves any conflicts, and clicks "Confirm Import".
7.  **System Action (Backend):**
    *   Receives confirmation and user's resolution choices.
    *   Applies the chosen actions (inserts new transactions, updates existing ones, skips ignored ones).
    *   Commits changes to the database.
8.  **System Action (Frontend):**
    *   Displays a success message or an import log with any remaining errors.
    *   Redirects user to their portfolio or transaction history.

## 6. Open Questions/Assumptions

*   **PDF Parsing Libraries:** What specific Python libraries will be used for PDF parsing (e.g., `pdfminer.six`, `camelot`, `tabula-py`)? This will require research and potentially external dependencies.
*   **HTML Parsing:** What specific Python libraries will be used for HTML parsing (e.g., `BeautifulSoup`, `lxml`)?
*   **Initial Focus:** Should we prioritize CSV import first, then move to PDF/HTML, or attempt all simultaneously? (Recommendation: Start with CSV as it's generally simpler, then add specific PDF/HTML parsers).
*   **Data Points:** Confirm the exact data points required for each transaction type (e.g., for dividends, do we need ex-date, record-date, pay-date, per-share amount, total amount?).
*   **Authentication for Broker APIs:** If any broker APIs require direct authentication (e.g., OAuth), this will add significant complexity and security considerations. (Assumption: For now, we are parsing *statements*, not directly integrating with live broker APIs for transaction data).
*   **Error Reporting:** How detailed should the error reporting be to the user? (e.g., "Line 15: Invalid date format" vs. "Parsing error in 'Date' column").

---
