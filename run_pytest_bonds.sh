cd backend
python3 -m pytest app/tests/api/v1/test_bonds.py -vv | grep -E "E\s+" | head -n 30
