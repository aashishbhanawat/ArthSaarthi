# Non-Functional Requirement: NFR14 - Android Deployment Stability

## 1. Objective
Ensure the ArthSaarthi backend is fully stable when running on Android via Chaquopy, where Pydantic v1 is the only available version, while maintaining compatibility with Pydantic v2 in the Desktop/Server environments.

## 2. Background
ArthSaarthi uses Pydantic extensively for data validation and serialization. The development and server environments use Pydantic v2, which introduced several breaking changes and new method names (e.g., `model_dump`, `model_validate`). Android/Chaquopy currently only supports Pydantic v1, leading to runtime `AttributeError` and `ResponseValidationError`.

## 3. Requirements

### 3.1. Unified Compatibility Interface
- A centralized utility module (`app/utils/pydantic_compat.py`) MUST provide wrapper functions for all common Pydantic operations.
- Supported operations:
    - `model_dump(obj, **kwargs)`: Replaces `.dict()` (v1) and `.model_dump()` (v2).
    - `model_dump_json(obj, **kwargs)`: Replaces `.json()` (v1) and `.model_dump_json()` (v2).
    - `model_validate(model, data, **kwargs)`: Replaces `model.parse_obj()` (v1) and `model.model_validate()` (v2).
    - `model_validate_json(model, json_str, **kwargs)`: Replaces `model.parse_raw()` (v1) and `model.model_validate_json()` (v2).
    - `model_copy(obj, **kwargs)`: Replaces `.copy()` (v1) and `.model_copy()` (v2).

### 3.2. Codebase Enforcement
- ALL direct calls to `.model_dump()`, `.model_validate()`, etc., in the `app/` directory (excluding the compatibility module itself) MUST be replaced with calls to the compatibility utility.
- Both production code and test code MUST adhere to this requirement to ensure test parity on Android.

### 3.3. Fallback Resilience
- The compatibility layer MUST detect the Pydantic version at runtime and route calls appropriately without performance overhead.

## 4. Verification
- Backend test suite MUST pass in the Pydantic v2 environment (Docker).
- Manual code audit MUST confirm zero direct v2 method calls remain.
- (Optional) Build the Android APK and verify runtime stability on an AArch64 device.
