import requests

url = "http://localhost:8000/api/v1/auth/login"

# Run multiple logins
for i in range(50):
    response = requests.post(url, data={"username": "test@example.com", "password": "wrong"})
    print(response.status_code)
