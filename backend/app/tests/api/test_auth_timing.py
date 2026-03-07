import time
from app.core.security import get_password_hash
from app.models.user import User

def test_login_timing_attack(client, db):
    import statistics
    import time

    # Create test user
    from app.crud.crud_user import user as user_crud
    from app.schemas.user import UserCreate

    test_user_in = UserCreate(email="test_timing@example.com", password="Correct_password123!", full_name="Test User")
    test_user = user_crud.create(db, obj_in=test_user_in, is_admin=False)
    db.commit()

    # 1. Time to authenticate an existing user with incorrect password
    times_existing = []
    for _ in range(10):
        start = time.time()
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test_timing@example.com", "password": "Wrongpassword123!"}
        )
        times_existing.append(time.time() - start)

    # 2. Time to authenticate a non-existing user
    times_non_existing = []
    for _ in range(10):
        start = time.time()
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@example.com", "password": "Wrongpassword123!"}
        )
        times_non_existing.append(time.time() - start)

    avg_existing = statistics.mean(times_existing)
    avg_non_existing = statistics.mean(times_non_existing)

    print(f"\nExisting user: {avg_existing:.4f}s")
    print(f"Non-existing user: {avg_non_existing:.4f}s")

    # Difference should be minimal (e.g. less than 10%)
    diff = abs(avg_existing - avg_non_existing)
    print(f"Difference: {diff:.4f}s")
