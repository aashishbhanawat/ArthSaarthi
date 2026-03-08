import re
with open("backend/app/crud/crud_holding.py", "r") as f:
    content = f.read()
if "from typing import " in content and "Dict" not in content:
    content = content.replace("from typing import ", "from typing import Dict, ")
with open("backend/app/crud/crud_holding.py", "w") as f:
    f.write(content)
