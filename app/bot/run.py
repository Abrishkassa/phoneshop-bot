"""Run the Telegram bot in polling mode — for local development.

Usage:
    python -m app.bot.run
"""
from app.bot.app import build_application


def main():
    application = build_application()
    print("Bot starting in polling mode... Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
