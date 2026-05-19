import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("AIzaSyCnEktCajN1SzlI5OUuqyN2hlxFdU6NZ7w"))

print("Models available to you:\n")
for m in client.models.list():
    for action in m.supported_actions:
        if action == "generateContent":
            print(m.name)
            break