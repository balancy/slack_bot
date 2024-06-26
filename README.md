# Slack bot

![bot](bot.png)

App represents bot for Slack application. It can answer in public chats if is invited and via private messages.

## Local installation and launch

You should have at least Git, Python3.10 and Docker installed in your system. You should also create a bot instance with correct permissions in your slack workspace.

1. Clone the git repository

```
git clone https://github.com/balancy/slack_bot.git
```

2. Copy file with environment variables and define them inside .env

```
cp .env.example .env
```
where
- `SLACK_BOT_TOKEN` - your slack bot token
- `SLACK_SIGNING_SECRET` - your slack signing secret
- `SLACK_CLIENT_ID` - your slack app client id
- `SLACK_CLIENT_SECRET` - your slack app client secret
- `HOST` - host of your app

3. Launch the app

```
make launch
```
