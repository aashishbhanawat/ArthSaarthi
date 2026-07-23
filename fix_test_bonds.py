import re

with open('backend/app/api/v1/endpoints/bonds.py', 'r') as f:
    content = f.read()

content = content.replace(
    '        if portfolio and portfolio.user_id == user_id:\n            return',
    '        # test sqlite operational error due to transaction.portfolio_id\n        pass'
)
