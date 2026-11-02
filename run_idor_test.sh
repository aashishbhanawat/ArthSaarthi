#!/bin/bash
docker compose run --rm backend sh -c "pip install -r requirements-dev.in && pytest app/tests/crud/test_transaction_crud_idor.py"
