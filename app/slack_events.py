"""Slack event handling functions"""

import hashlib
import hmac
import logging

from fastapi import HTTPException, Request
from slack_sdk.errors import SlackApiError
from slack_sdk.web.client import WebClient

logger = logging.getLogger(__name__)


def verify_slack_request(request: Request, signing_secret: str) -> None:
    """Verify incoming Slack requests."""
    body = await request.body()
    timestamp = request.headers["X-Slack-Request-Timestamp"]
    slack_signature = request.headers["X-Slack-Signature"]

    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    secret = bytes(signing_secret, "utf-8")

    my_signature = (
        "v0=" + hmac.new(secret, basestring.encode("utf-8"), hashlib.sha256).hexdigest()
    )

    if not hmac.compare_digest(my_signature, slack_signature):
        logger.warning("Request verification failed")
        raise HTTPException(status_code=403, detail="Request verification failed")


async def handle_event(payload: dict, bot_token: str) -> None:
    """Handle incoming Slack events."""
    client = WebClient(token=bot_token)
    event = payload.get("event", {})
    if event.get("type") == "app_mention":
        channel_id = event.get("channel")
        user_message = event.get("text")
        response_message = f"You said: {user_message}"

        try:
            await client.chat_postMessage(channel=channel_id, text=response_message)
        except SlackApiError as e:
            logger.error(f"Error posting message: {e.response['error']}")
