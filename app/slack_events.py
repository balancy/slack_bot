"""Slack event handling functions."""

import hashlib
import hmac
import logging
import re

import httpx
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.chatgpt import ask_chatgpt
from app.constants import SUCCESSFUL_STATUS_CODE
from app.models import Team

logger = logging.getLogger(__name__)


async def verify_slack_request(request: Request, signing_secret: str) -> None:
    """
    Verify incoming Slack requests.

    Args:
    ----
        request: The incoming request.
        signing_secret: The Slack signing secret.

    """
    headers = request.headers
    logger.info(f"Headers: {headers}")

    if "X-Slack-Request-Timestamp" not in headers:
        logger.error("X-Slack-Request-Timestamp header missing")
        raise HTTPException(
            status_code=400,
            detail="Bad Request: Missing required headers",
        )

    body = await request.body()
    timestamp = headers["X-Slack-Request-Timestamp"]
    slack_signature = headers["X-Slack-Signature"]

    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    secret = bytes(signing_secret, "utf-8")

    my_signature = (
        "v0="
        + hmac.new(
            secret,
            basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )

    if not hmac.compare_digest(my_signature, slack_signature):
        logger.warning("Request verification failed")
        raise HTTPException(
            status_code=403,
            detail="Request verification failed",
        )


async def post_message(
    channel_id: str,
    response_message: str,
    bot_token: str,
) -> None:
    """
    Post a message to a Slack channel.

    Args:
    ----
        channel_id: The channel ID.
        response_message: The message to post.
        bot_token: The bot token.

    """
    try:
        logger.info(f"Posting message to channel: {channel_id}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bot_token}",
        }
        message_payload = {
            "channel": channel_id,
            "text": response_message,
        }
        async with httpx.AsyncClient() as http_client:
            result = await http_client.post(
                "https://slack.com/api/chat.postMessage",
                json=message_payload,
                headers=headers,
            )
            logger.info(f"Response from Slack API: {result.json()}")
            if (
                result.status_code != SUCCESSFUL_STATUS_CODE
                or not result.json().get("ok", False)
            ):
                logger.error(f"Error posting message: {result.json()}")
            else:
                logger.info("Message posted successfully.")
    except Exception:
        logger.exception("Error posting message")


async def handle_event(payload: dict, db: Session) -> None:
    """
    Handle incoming Slack events.

    Args:
    ----
        payload: The incoming event payload.
        db: The database session.

    """
    event = payload.get("event", {})
    team_id = payload.get("team_id")

    if not (event.get("type") == "message" and "subtype" not in event):
        return

    if event.get("bot_id") is not None:
        logger.info("Ignoring bot's own message")
        return

    channel_id = event.get("channel")
    user_message = event.get("text")

    cleaned_message = re.sub(r"<@U[A-Z0-9]+>", "", user_message).strip()

    response_message = await ask_chatgpt(cleaned_message)

    logger.info(f"Event: {event}")
    logger.info(f"Channel ID from event: {channel_id}")

    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        logger.error(f"Team not found for team_id: {team_id}")
        return

    bot_token = team.access_token

    await post_message(channel_id, response_message, str(bot_token))
