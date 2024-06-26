"""Main module for the FastAPI application."""

from __future__ import annotations

import logging

from environs import Env
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.slack_commands import handle_command
from app.slack_events import handle_event, verify_slack_request

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = Env()
env.read_env()

BOT_TOKEN = env.str("SLACK_BOT_TOKEN")
SIGNING_SECRET = env.str("SLACK_SIGNING_SECRET")
CLIENT_ID = env.str("SLACK_CLIENT_ID")
CLIENT_SECRET = env.str("SLACK_CLIENT_SECRET")
HOST = env.str("HOST")

templates = Jinja2Templates(directory="templates")


class SlackEvent(BaseModel):
    type: str
    challenge: str | None = None


@app.post("/slack/events")
async def slack_events(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str | None]:
    """Handle incoming Slack events."""
    body = await request.json()
    event = SlackEvent(**body)

    if event.type == "url_verification":
        return {"challenge": event.challenge}

    await verify_slack_request(request, SIGNING_SECRET)
    background_tasks.add_task(handle_event, body, BOT_TOKEN)
    return {"status": "ok"}


@app.post("/slack/commands")
async def slack_commands(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle incoming Slack commands."""
    await verify_slack_request(request, SIGNING_SECRET)
    payload: dict = dict(await request.form())
    background_tasks.add_task(handle_command, payload, BOT_TOKEN)
    return {"status": "ok"}


@app.get("/slack/oauth/callback")
async def oauth_callback(request: Request) -> RedirectResponse:
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse(url=f"{HOST}/error?message=No%20code%20provided")

    client = WebClient()

    try:
        response = client.oauth_v2_access(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            code=code,
            redirect_uri=f"{HOST}/slack/oauth/callback",
        )
        return RedirectResponse(url=f"{HOST}/success?team={response['team']['name']}")
    except SlackApiError as e:
        logger.error(f"Slack API error: {str(e)}")
        return RedirectResponse(url=f"{HOST}/error?message={str(e)}")


@app.get("/success", response_class=HTMLResponse)
async def success(request: Request, team: str):
    return templates.TemplateResponse(
        "success.html", {"request": request, "team": team}
    )


@app.get("/error", response_class=HTMLResponse)
async def error(request: Request, message: str):
    return templates.TemplateResponse(
        "error.html", {"request": request, "message": message}
    )


if __name__ == "__main__":
    logger.info("Starting server...")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
