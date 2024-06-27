"""Main module for the FastAPI application."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Generator

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.environment import CLIENT_ID, CLIENT_SECRET, HOST, SIGNING_SECRET
from app.models import SessionLocal, Team
from app.slack_commands import handle_command
from app.slack_events import handle_event, verify_slack_request

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


templates = Jinja2Templates(directory="templates")


class SlackEvent(BaseModel):
    """Slack event model."""

    type: str
    challenge: str | None = None


def get_db() -> Generator[Session, Any, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/slack/events")
async def slack_events(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session | None = None,
) -> dict[str, str | None]:
    """
    Handle incoming Slack events.

    Args:
    ----
        request: The incoming request.
        background_tasks: The background tasks.
        db: The database session.

    """
    session: Session = db or Depends(get_db)

    body = await request.json()
    event = SlackEvent(**body)

    if event.type == "url_verification":
        return {"challenge": event.challenge}

    await verify_slack_request(request, SIGNING_SECRET)
    background_tasks.add_task(handle_event, body, session)
    return {"status": "ok"}


@app.post("/slack/commands")
async def slack_commands(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session | None = None,
) -> dict[str, str]:
    """
    Handle incoming Slack commands.

    Args:
    ----
        request: The incoming request.
        background_tasks: The background tasks.
        db: The database session.

    """
    session: Session = db or Depends(get_db)

    await verify_slack_request(request, SIGNING_SECRET)
    payload: dict = dict(await request.form())
    background_tasks.add_task(handle_command, payload, session)
    return {"status": "ok"}


@app.get("/slack/oauth/callback")
async def oauth_callback(
    request: Request,
    db: Session | None = None,
) -> HTMLResponse:
    """
    Handle the OAuth callback from Slack.

    Args:
    ----
        request: The incoming request.
        db: The database session.

    """
    session: Session = db or Depends(get_db)
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{HOST}/slack/oauth/callback",
            },
        )
        data = response.json()
        if not data.get("ok"):
            raise HTTPException(status_code=400, detail=data.get("error"))

        access_token = data["access_token"]
        team_id = data["team"]["id"]
        team_name = data["team"]["name"]

        team = session.query(Team).filter(Team.team_id == team_id).first()
        if team:
            team.access_token = access_token
            team.team_name = team_name
        else:
            team = Team(
                team_id=team_id,
                team_name=team_name,
                access_token=access_token,
            )
            session.add(team)
        session.commit()

        return HTMLResponse(
            content=f"App successfully installed in team: {team_name}",
        )
