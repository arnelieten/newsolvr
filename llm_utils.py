import json
from google import genai

def llm_call(input):
    with open("llm_api_credentials.json", "r") as f:
            headers = json.load(f)
            API_KEY = headers['api-key']
        
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=input
    )
    print(response.text)