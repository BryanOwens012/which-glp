#!/usr/bin/env python3
"""Minimal test of the OpenAI SDK (GPT-6 Luna) to verify connectivity.

GPT-6 Luna is a reasoning model: it does NOT accept sampling parameters
(temperature, top_p, etc.). Use reasoning_effort instead.
Docs: https://developers.openai.com/api/docs/models/gpt-6-luna
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {api_key[:20]}...")

client = OpenAI(api_key=api_key)
print("Client created successfully")

print("\nTesting with gpt-6-luna...")
try:
    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {"role": "user", "content": "Say 'hello' and nothing else."}
        ],
        reasoning_effort="none",
    )
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens: {response.usage.prompt_tokens}/{response.usage.completion_tokens}")
except Exception as e:
    print(f"ERROR with gpt-6-luna: {e}")
