"""Slack event handling functions"""

import hashlib
import hmac
import logging

from fastapi import HTTPException, Request
from slack_sdk.errors import SlackApiError
from slack_sdk.web.client import WebClient

logger = logging.getLogger(__name__)


async def verify_slack_request(request: Request, signing_secret: str) -> None:
    """Verify incoming Slack requests."""
    headers = request.headers
    logger.info(f"Headers: {headers}")

    if "X-Slack-Request-Timestamp" not in headers:
        logger.error("X-Slack-Request-Timestamp header missing")
        raise HTTPException(
            status_code=400, detail="Bad Request: Missing required headers"
        )

    body = await request.body()
    timestamp = headers["X-Slack-Request-Timestamp"]
    slack_signature = headers["X-Slack-Signature"]

    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    secret = bytes(signing_secret, "utf-8")

    my_signature = (
        "v0=" + hmac.new(secret, basestring.encode("utf-8"), hashlib.sha256).hexdigest()
    )

    if not hmac.compare_digest(my_signature, slack_signature):
        logger.warning("Request verification failed")
        raise HTTPException(status_code=403, detail="Request verification failed")


def handle_event(payload: dict, bot_token: str) -> None:
    """Handle incoming Slack events."""
    client = WebClient(token=bot_token)
    event = payload.get("event", {})

    if event.get("type") == "message" and "subtype" not in event:
        if event.get("bot_id") is not None:
            logger.info("Ignoring bot's own message")
            return

        channel_id = event.get("channel")
        user_message = event.get("text")
        response_message = f"You said: {user_message}"

        try:
            logger.info(f"Attempting to post message to channel ID: {channel_id}")
            response = client.chat_postMessage(channel=channel_id, text=response_message)
            logger.info(f"Message posted successfully: {response}")
        except SlackApiError as e:
            logger.error(f"Error posting message: {e.response['error']}")
            logger.error(f"Payload: {payload}")
            logger.error(f"Event: {event}")
            if e.response['error'] == 'channel_not_found':
                logger.error("The bot might not be a member of the channel. Please invite the bot to the channel.")
            elif e.response['error'] == 'not_in_channel':
                logger.error("The bot is not in the channel. Please ensure the bot is invited to the channel.")
            elif e.response['error'] == 'is_archived':
                logger.error("The channel is archived and cannot be posted to.")
            elif e.response['error'] == 'msg_too_long':
                logger.error("The message is too long to be posted.")
            else:
                logger.error(f"Unexpected error: {e.response['error']}")