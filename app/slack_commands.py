"""Slack bot commands."""

import logging

import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.orm import Session

from .chatgpt import call_chatgpt
from .models import Team

logger = logging.getLogger(__name__)


async def handle_command(payload: dict, db: Session) -> None:
    """Handle incoming Slack commands."""
    command = payload.get("command")
    text = payload.get("text")
    response_url = str(payload.get("response_url"))
    team_id = payload.get("team_id")

    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        logger.error(f"Team not found for team_id: {team_id}")
        return

    bot_token = team.access_token

    if command != "/call_panda":
        return

    if not text:
        response_message = "You should write some text after calling panda."
    else:
        response_message = await call_chatgpt(text)

    try:
        logger.info(f"Responding to command in response_url: {response_url}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bot_token}",
        }

        async with httpx.AsyncClient() as http_client:
            result = await http_client.post(
                response_url, json={"text": response_message}, headers=headers
            )

        if result.status_code != 200:
            logger.error(f"Error posting message: {result.text}")
    except SlackApiError as e:
        logger.error(f"Error posting message: {e.response['error']}")

    channel_id = payload.get("channel_id")

    if channel_id:
        client = WebClient(token=str(bot_token))
        try:
            response = client.chat_postMessage(
                channel=channel_id, text=response_message
            )
            logger.info(f"Message posted successfully: {response}")
        except SlackApiError as e:
            logger.error(f"Error posting message: {e.response['error']}")
