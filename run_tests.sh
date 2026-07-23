source /home/jules/.pyenv/versions/3.12.13/bin/activate || true
export TESTING=1
export DATABASE_URL=sqlite:///./test.db
cd backend
python -m pytest app/tests/api/v1/test_bonds.py -vv | grep -E "E\s+" | head -n 30
