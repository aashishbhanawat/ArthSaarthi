import requests

url = "http://localhost:8000/api/v1/auth/login"

response = requests.post(url, data={"username": "test@example.com", "password": "wrong"})
print(response.status_code)
