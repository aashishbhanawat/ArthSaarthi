# BUG: FD Reinvestment Calculation Issues

**Status**: ✅ Fixed  
**Date**: 2025-12-31

## Description
Cumulative Fixed Deposit (FD) shows incorrect "Realized Gain" instead of "Unrealized Gain", and maturity value calculation was broken.

## Root Cause
Case-sensitivity bugs in FD calculation functions:
- `_calculate_total_interest_paid()` checked for `"Cumulative"` but DB stores `"CUMULATIVE"`
- `_calculate_fd_current_value()` checked for `"Cumulative"` and title-case compounding frequencies

## Symptoms
1. Realized Gain shows non-zero for cumulative FDs (should be 0 until maturity)
2. Current Value calculated incorrectly for cumulative FDs
3. Maturity value not calculated properly for reinvestment FDs

## Fix Applied
- Made payout type check case-insensitive: `(fd.interest_payout or "").upper() == "CUMULATIVE"`
- Made compounding frequency map use uppercase keys and normalized input
- Defaulted compounding to quarterly (4) instead of annually (1)

## Files Changed
- `backend/app/crud/crud_holding.py`:
  - `_calculate_total_interest_paid()` (line 59)
  - `_calculate_fd_current_value()` (lines 37, 43-49)

## Verification
- Cumulative FD should show Realized Gain: ₹0.00
- Current Value should reflect compound interest calculation
- Maturity Value should project full interest at maturity
