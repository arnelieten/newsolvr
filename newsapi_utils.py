import requests
import json

def api_call(topic):
    base_url = "https://newsapi.org/v2/everything"

    with open("api_credentials.json", "r") as f:
        headers = json.load(f)

    params = {
        "q" : topic,
        "language" : "en"
    }

    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        news_data = response.json()
        return news_data
    else:
        print(f"Failed to connect with API {response.status_code}")