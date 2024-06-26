"""Slack bot commands."""

import logging

import httpx
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


async def handle_command(payload: dict, bot_token: str) -> None:
    """Handle incoming Slack commands."""
    command = payload.get("command")
    text = payload.get("text")
    response_url = str(payload.get("response_url"))

    if command == "/call_panda":
        response_message = f"You asked: {text}"
        try:
            logger.info(f"Responding to command in response_url: {response_url}")
            async with httpx.AsyncClient() as http_client:
                result = await http_client.post(response_url, json={"text": response_message})

            if result.status_code != 200:
                logger.error(f"Error posting message: {result.text}")
        except SlackApiError as e:
            logger.error(f"Error posting message: {e.response['error']}")
