import re

with open('backend/app/tests/api/v1/test_bonds_security.py', 'r') as f:
    content = f.read()

content = content.replace(
    'response = client.get(\n        f"{settings.API_V1_STR}/portfolios/{portfolio_a.id}/bonds/{bond.id}", # Just dummy portfolio ID\n        headers=headers_b,\n    )',
    'response = client.get(\n        f"{settings.API_V1_STR}/bonds/{bond.id}",\n        headers=headers_b,\n    )'
)

with open('backend/app/tests/api/v1/test_bonds_security.py', 'w') as f:
    f.write(content)
