# brokeapi.py
import requests

class BrokeAPI:
    BASE_URL = "http://51.195.119.116:11479/chat"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key

    def send_prompt(self, prompt: str) -> dict:
        if not prompt:
            raise ValueError("Prompt is required")

        params = {
            "key": self.api_key,
            "prompt": prompt
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"BrokeAPI request failed: {e}")
