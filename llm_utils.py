import json
from google import genai

with open("llm_api_credentials.json", "r") as f:
        headers = json.load(f)
        API_KEY = headers['api-key']
    
client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="Gemini 2.5 Flash Preview 05-20", contents="Explain how AI works in a few words"
)
print(response.text)