# BrokeAPI

A simple and lightweight Python client for interacting with the BrokeAPI chat API.

This module lets you easily send prompts and receive AI-generated replies with simple method calls.

---

## Installation

```bash
pip install brokeapi
```

## Usage
```py
from brokeapi import BrokeAPI

# Initialize the API client with your API key
api = BrokeAPI('YOUR_KEY_HERE')

try:
    # Send a prompt to the BrokeAPI chat endpoint
    response = api.send_prompt('Hello from Python!')

    # Print the reply text from the API
    print('BrokeAPI reply:\n', response.get('reply'))
except Exception as err:
    print('Error:', err)
```

# How to get key?
To get an API key, join our official [Discord server]([text](https://discord.gg/ez3sgB8TRj)).