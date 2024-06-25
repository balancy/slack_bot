"""Main module for the FastAPI application."""

from __future__ import annotations

import logging

from environs import Env
from fastapi import BackgroundTasks, FastAPI, Request

from app.slack_commands import handle_command
from app.slack_events import handle_event, verify_slack_request

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = Env()
env.read_env()

app.state.bot_token = env.str("SLACK_BOT_TOKEN")
app.state.signing_secret = env.str("SLACK_SIGNING_SECRET")


@app.post("/slack/events")
async def slack_events(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle incoming Slack events."""
    await verify_slack_request(request, app.state.signing_secret)
    payload = await request.json()
    background_tasks.add_task(handle_event, payload, app.state.bot_token)
    return {"status": "ok"}


@app.post("/slack/commands")
async def slack_commands(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """Handle incoming Slack commands."""
    await verify_slack_request(request, app.state.signing_secret)
    payload = await request.form()
    background_tasks.add_task(handle_command, payload, app.state.bot_token)
    return {"status": "ok"}


if __name__ == "__main__":
    logger.info("Starting server...")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
