"""Module for calling chatgpt."""

import logging

import httpx

from app.environment import OPENAI_API_KEY

logger = logging.getLogger(__name__)


async def ask_chatgpt(prompt: str) -> str:
    """Ask the ChatGPT model a question.

    Args:
    ----
        prompt: The user's input.

    """
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
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 50,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        response_json = response.json()

        if response_json.get("choices"):
            return response_json["choices"][0]["message"]["content"].strip()
        else:
            return "Sorry, I couldn't process your request."
