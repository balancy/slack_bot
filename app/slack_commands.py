"""Slack bot commands."""

import logging

from slack_sdk.errors import SlackApiError
from slack_sdk.web.client import WebClient

logger = logging.getLogger(__name__)


async def handle_command(payload: dict, bot_token: str) -> None:
    """Handle incoming Slack commands."""
    client = WebClient(token=bot_token)
    command = payload.get("command")
    text = payload.get("text")
    response_url = payload.get("response_url")

    if command == "/call_panda":
        response_message = f"You asked: {text}"
        try:
            logger.info(f"Responding to command in response_url: {response_url}")
            client.chat_postMessage(channel=str(response_url), text=response_message)
        except SlackApiError as e:
            logger.error(f"Error posting message: {e.response['error']}")
