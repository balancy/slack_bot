"""Module for reading environment variables."""

from environs import Env

env = Env()
env.read_env()

SIGNING_SECRET = env.str("SLACK_SIGNING_SECRET")
CLIENT_ID = env.str("SLACK_CLIENT_ID")
CLIENT_SECRET = env.str("SLACK_CLIENT_SECRET")
HOST = env.str("HOST")
OPENAI_API_KEY = env.str("OPENAI_API_KEY")
OPENAI_TEMPERATURE = env.float("OPENAI_TEMPERATURE", 0.7)
OPENAI_MODEL = env.str("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_MAX_TOKENS = env.int("OPENAI_MAX_TOKENS", 50)
