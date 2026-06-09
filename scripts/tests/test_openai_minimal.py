#!/usr/bin/env python3
"""Minimal test of the OpenAI SDK (GPT-5-nano) to verify connectivity.

GPT-5-nano is a reasoning model: it does NOT accept sampling parameters
(temperature, top_p, etc.). Use reasoning_effort instead.
Docs: https://developers.openai.com/api/docs/models/gpt-5-nano
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {api_key[:20]}...")

client = OpenAI(api_key=api_key)
print("Client created successfully")

print("\nTesting with gpt-5-nano...")
try:
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "user", "content": "Say 'hello' and nothing else."}
        ],
        reasoning_effort="minimal",
    )
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens: {response.usage.prompt_tokens}/{response.usage.completion_tokens}")
except Exception as e:
    print(f"ERROR with gpt-5-nano: {e}")
