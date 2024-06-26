"""Module for calling chatgpt."""

import logging

import httpx

from .environment import OPENAI_API_KEY

logger = logging.getLogger(__name__)


async def ask_chatgpt(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 50,
            },
        )
        response.raise_for_status()
        response_json = response.json()

        if "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0]["message"]["content"].strip()
        else:
            return "Sorry, I couldn't process your request."
