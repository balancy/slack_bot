"""Module for reading environment variables."""
from environs import Env

env = Env()
env.read_env()

SIGNING_SECRET = env.str("SLACK_SIGNING_SECRET")
CLIENT_ID = env.str("SLACK_CLIENT_ID")
CLIENT_SECRET = env.str("SLACK_CLIENT_SECRET")
HOST = env.str("HOST")
OPENAI_API_KEY = env.str("OPENAPI_API_KEY")