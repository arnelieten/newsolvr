import requests
import json

base_url = "https://api.openaq.org/v3/locations/8118"

with open("api_credentials.json", "r") as f:
    headers = json.load(f)

response = requests.get(base_url, headers=headers)

print(f"Status Code: {response.status_code}")
print(response.json())