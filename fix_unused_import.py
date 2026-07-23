import re

with open('backend/app/crud/crud_ppf.py', 'r') as f:
    content = f.read()

content = content.replace("from app import crud, models, schemas", "from app import crud, schemas")

with open('backend/app/crud/crud_ppf.py', 'w') as f:
    f.write(content)
