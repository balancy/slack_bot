"""Main module for the FastAPI application."""

from __future__ import annotations

import logging
from typing import Any, Generator

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.slack_commands import handle_command
from app.slack_events import handle_event, verify_slack_request

from .environment import CLIENT_ID, CLIENT_SECRET, HOST, SIGNING_SECRET
from .models import SessionLocal, Team

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



templates = Jinja2Templates(directory="templates")


class SlackEvent(BaseModel):
    type: str
    challenge: str | None = None


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/slack/events")
async def slack_events(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> dict[str, str | None]:
    """Handle incoming Slack events."""
    body = await request.json()
    event = SlackEvent(**body)

    if event.type == "url_verification":
        return {"challenge": event.challenge}

    await verify_slack_request(request, SIGNING_SECRET)
    background_tasks.add_task(handle_event, body, db)
    return {"status": "ok"}


@app.post("/slack/commands")
async def slack_commands(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> dict[str, str]:
    """Handle incoming Slack commands."""
    await verify_slack_request(request, SIGNING_SECRET)
    payload: dict = dict(await request.form())
    background_tasks.add_task(handle_command, payload, db)
    return {"status": "ok"}


@app.get("/slack/oauth/callback")
async def oauth_callback(
    request: Request, db: Session = Depends(get_db)
) -> HTMLResponse:
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

        team = db.query(Team).filter(Team.team_id == team_id).first()
        if team:
            team.access_token = access_token
            team.team_name = team_name
        else:
            team = Team(team_id=team_id, team_name=team_name, access_token=access_token)
            db.add(team)
        db.commit()

        return HTMLResponse(content=f"App successfully installed in team: {team_name}")


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
