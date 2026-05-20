# test_gemini.py
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Sending test request...")
start = time.time()

response = client.models.generate_content(
    model="gemini-3.1-flash-lite-preview",
    contents="Reply with just the word HELLO",
)

elapsed = time.time() - start
print(f"Response: {response.text}")
print(f"Time taken: {elapsed:.2f} seconds")