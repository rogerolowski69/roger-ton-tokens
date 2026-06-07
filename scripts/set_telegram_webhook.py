from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]
API_BASE_URL = os.environ["API_BASE_URL"].rstrip("/")
MINI_APP_URL = os.environ["MINI_APP_URL"]

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_URL = f"{API_BASE_URL}/api/webhooks/telegram"


def post(method: str, payload: dict):
    r = httpx.post(f"{TG_API}/{method}", json=payload, timeout=20)
    data = r.json()

    if not data.get("ok"):
        raise SystemExit(data)

    return data["result"]


def main() -> None:
    webhook = post(
        "setWebhook",
        {
            "url": WEBHOOK_URL,
            "secret_token": WEBHOOK_SECRET,
            "drop_pending_updates": True,
            "allowed_updates": [
                "message",
                "callback_query",
                "pre_checkout_query",
            ],
        },
    )

    menu = post(
        "setChatMenuButton",
        {
            "menu_button": {
                "type": "web_app",
                "text": "Open App",
                "web_app": {"url": MINI_APP_URL},
            }
        },
    )

    commands = post(
        "setMyCommands",
        {
            "commands": [
                {"command": "start", "description": "Open menu"},
                {"command": "app", "description": "Open Mini App"},
                {"command": "balance", "description": "Store credit balance"},
                {"command": "buy_credit", "description": "Buy $1 credit"},
                {"command": "buy_hour", "description": "Buy 1-hour voucher"},
                {"command": "help", "description": "Help"},
            ]
        },
    )

    info = post("getWebhookInfo", {})

    print(
        {
            "webhook": webhook,
            "menu": menu,
            "commands": commands,
            "webhook_info": info,
        }
    )


if __name__ == "__main__":
    main()
