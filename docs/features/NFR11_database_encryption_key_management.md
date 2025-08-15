# Feature Plan: Database Encryption Key Management (NFR11)

## 1. Scope & Context

**This encryption plan applies *exclusively* to the single-user, native desktop executable deployment of ArthSaarthi.** It provides data-at-rest protection for the local SQLite database file.

## 2. Objective
To design and implement a secure method for managing the encryption key for the local SQLite database, ensuring a robust, self-contained solution that does not require external C-libraries or compilers on the user's machine.

## 3. The Challenge: Finding a Self-Contained Encryption Method
- **Full Database Encryption is Problematic:** Libraries that provide full, transparent encryption for SQLite (like `pysqlcipher`) require compiling C-code and linking against the `sqlcipher` library. This would force end-users to install developer tools, defeating the purpose of a one-click installer.
- **File-Level Encryption is Risky:** Encrypting the entire database file in Python before use and after closing is risky. It can lead to data loss if the application crashes and has poor performance with large databases.

## 4. The Solution: Column-Level Encryption with SQLAlchemy `TypeDecorator`
We will adopt a **Column-Level Encryption** strategy. This approach is fully self-contained, performant, and secure.

1.  **Technology:** We will use the `cryptography` library, which ships with pre-compiled binary wheels for all major operating systems, ensuring no end-user installation steps are needed.
2.  **Implementation:** We will use a powerful SQLAlchemy pattern called `TypeDecorator`. We will create a custom `EncryptedString` data type that wraps the standard `String` type.
    *   When our application saves data to a column with this type, the decorator will automatically encrypt the value using our master key.
    *   When the data is read, it will be automatically decrypted.
    *   This keeps the encryption logic transparent to the rest of the application (e.g., CRUD operations).
3.  **Key Management (Envelope Encryption):** The strategy for managing the *master key* itself remains the same as the original plan.
    *   A single, strong, randomly generated `MASTER_KEY` is used for all column encryption/decryption.
    *   The user's password is used to derive a `WRAPPING_KEY`.
    *   The `MASTER_KEY` is encrypted with the `WRAPPING_KEY` and the result is stored in a configuration file. The `MASTER_KEY` itself only ever exists in memory during a user's session.

## 5. User Flow & Key Management

### 5.1. Initial Setup
1.  User creates an account with a password.
2.  The backend generates a new, random `MASTER_KEY`.
3.  The backend derives a `WRAPPING_KEY` from the user's password.
4.  The backend encrypts the `MASTER_KEY` and saves it to a file.
5.  The backend holds the `MASTER_KEY` in memory for the session.

### 5.2. User Login
1.  User provides their password.
2.  The backend derives the `WRAPPING_KEY` from the password.
3.  It attempts to decrypt the stored `ENCRYPTED_MASTER_KEY`.
    -   **Success:** The backend now has the `MASTER_KEY` in memory. All subsequent database operations that read or write to columns of type `EncryptedString` will now work automatically.
    -   **Failure:** An authentication error is returned.

### 5.3. Password Change
1.  User provides their old and new passwords.
2.  The backend uses the old password to decrypt the `MASTER_KEY`.
3.  It re-encrypts the same `MASTER_KEY` with a new `WRAPPING_KEY` derived from the new password.
4.  The database's encrypted data is never touched, making the process fast and secure.

## 6. Implementation Plan
1.  Create a `KeyManager` class to handle the envelope encryption of the master key.
2.  Implement a custom SQLAlchemy `TypeDecorator` called `EncryptedString` that uses the `KeyManager` to perform encryption and decryption.
3.  Apply the `EncryptedString` type to sensitive PII columns in the database models (e.g., `User.email`, `User.full_name`).
4.  Refactor the application startup and login logic for the desktop build to accommodate this key management flow.
5.  Create a `change-password` API endpoint to allow re-wrapping the master key.
