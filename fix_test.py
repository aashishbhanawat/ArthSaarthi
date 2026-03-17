import re

with open('backend/app/tests/api/v1/test_bonds_security.py', 'r') as f:
    content = f.read()

content = content.replace(
    'f"{settings.API_V1_STR}/portfolios/{user_a.id}/bonds/{bond.id}", # Just dummy portfolio ID',
    'f"{settings.API_V1_STR}/portfolios/{user_a.id}/bonds/{bond.id}",\n        # Just dummy portfolio ID'
)

with open('backend/app/tests/api/v1/test_bonds_security.py', 'w') as f:
    f.write(content)
