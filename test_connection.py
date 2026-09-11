import os
import requests
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

headers = {"Authorization": f"Bearer {hf_token}"}
payload = {
    "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "messages": [{"role": "user", "content": "What is C?"}]
}

try:
    response = requests.post(
        "https://api-inference.huggingface.co/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=15
    )
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Connection failed:", e)