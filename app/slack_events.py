"""Slack event handling functions"""

import hashlib
import hmac
import logging

import httpx
from fastapi import HTTPException, Request

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


async def handle_event(payload: dict, bot_token: str) -> None:
    """Handle incoming Slack events."""
    event = payload.get("event", {})

    if event.get("type") == "message" and "subtype" not in event:
        if event.get("bot_id") is not None:
            logger.info("Ignoring bot's own message")
            return

        channel_id = event.get("channel")
        user_message = event.get("text")
        response_message = f"You said: {user_message}"

        logger.info(f"Event: {event}")
        logger.info(f"Channel ID from event: {channel_id}")

        try:
            logger.info(f"Checking membership for channel: {channel_id}")
            async with httpx.AsyncClient() as http_client:
                membership_check = await http_client.post(
                    "https://slack.com/api/conversations.members",
                    headers={"Authorization": f"Bearer {bot_token}"},
                    params={"channel": channel_id}
                )
                membership_response = membership_check.json()
                logger.info(f"Membership check response: {membership_response}")
                if 'members' not in membership_response or not membership_response.get("ok", False):
                    logger.error(f"Failed to retrieve members for channel: {channel_id}")
                    return

                if bot_token not in membership_response["members"]:
                    logger.error(f"Bot is not a member of the channel: {channel_id}")
                    return

            logger.info(f"Posting message to channel: {channel_id}")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bot_token}",
            }

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
                if result.status_code != 200 or not result.json().get("ok", False):
                    logger.error(f"Error posting message: {result.json()}")
                else:
                    logger.info("Message posted successfully.")
        except Exception as e:
            logger.error(f"Error posting message: {str(e)}")

    elif event.get("type") == "member_joined_channel":
        channel_id = event["channel"]
        user_id = event["user"]
        logger.info(f"User {user_id} joined channel: {channel_id}")
