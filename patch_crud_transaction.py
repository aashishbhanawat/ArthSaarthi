import sys
import re

with open("backend/app/crud/crud_transaction.py", "r") as f:
    content = f.read()

# Pattern for the duplicated block
pattern = r"""    def get_multi_by_portfolios\(
        self, db: Session, \*, portfolio_ids: List\[uuid\.UUID\]
    \) -> List\[Transaction\]:
        return \(
            db\.query\(self\.model\)\.filter\(self\.model\.portfolio_id\.in_\(portfolio_ids\)\)\.all\(\)
        \)
"""

# Count occurrences
occurrences = len(re.findall(pattern, content))
print(f"Found {occurrences} occurrences")

# Replace all with empty, then put back exactly one
content = re.sub(pattern, "", content)

# Insert the single one where it belongs (e.g. before get_multi_by_portfolio)
lines = content.split('\n')
for i, line in enumerate(lines):
    if "def get_multi_by_portfolio(" in line:
        insert_idx = i
        break

lines.insert(insert_idx, """    def get_multi_by_portfolios(
        self, db: Session, *, portfolio_ids: List[uuid.UUID]
    ) -> List[Transaction]:
        return (
            db.query(self.model).filter(self.model.portfolio_id.in_(portfolio_ids)).all()
        )
""")

with open("backend/app/crud/crud_transaction.py", "w") as f:
    f.write("\n".join(lines))

print("Patched transaction")
