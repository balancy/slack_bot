"""Module for calling chatgpt."""

import logging

import httpx

from .environment import OPENAI_API_KEY

logger = logging.getLogger(__name__)

async def call_chatgpt(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "text-ada-001",
                "prompt": prompt,
                "max_tokens": 150,
            },
        )
        response.raise_for_status()
        response_json = response.json()
        logger.info(f"Response from OpenAI: {response_json}")

        return response_json["choices"][0]["text"].strip()
