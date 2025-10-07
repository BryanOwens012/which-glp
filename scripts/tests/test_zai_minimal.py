#!/usr/bin/env python3
"""Minimal test of ZAI SDK based on official docs."""

import os
from dotenv import load_dotenv
from zai import ZaiClient

load_dotenv()

api_key = os.getenv("GLM_API_KEY")
print(f"API Key found: {api_key[:20]}...")

client = ZaiClient(api_key=api_key)
print("Client created successfully")

print("\nTesting with glm-4.5-air...")
try:
    response = client.chat.completions.create(
        model="glm-4.5-air",
        messages=[
            {"role": "user", "content": "Say 'hello' and nothing else."}
        ],
        temperature=0
    )
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens: {response.usage.prompt_tokens}/{response.usage.completion_tokens}")
except Exception as e:
    print(f"ERROR with glm-4.5-air: {e}")

print("\nTesting with glm-4.6...")
try:
    response = client.chat.completions.create(
        model="glm-4.6",
        messages=[
            {"role": "user", "content": "Say 'hello' and nothing else."}
        ]
    )
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR with glm-4.6: {e}")
