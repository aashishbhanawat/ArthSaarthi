import py_compile
import sys

files = [
    "backend/app/crud/crud_transaction.py",
    "backend/app/crud/crud_fixed_deposit.py",
    "backend/app/crud/crud_recurring_deposit.py",
    "backend/app/crud/crud_asset.py"
]

for file in files:
    try:
        py_compile.compile(file, doraise=True)
        print(f"Syntax OK: {file}")
    except Exception as e:
        print(f"Syntax Error in {file}: {e}")
        sys.exit(1)
