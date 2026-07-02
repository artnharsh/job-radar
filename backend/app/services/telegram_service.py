"""
Telegram alert service — Day 5.

Sends immediate alerts when a watched company posts a new job.
Gracefully no-ops if TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured.

Uses python-telegram-bot (already in requirements.txt).
"""

from app.utils.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


async def send_watchlist_alert(
    company: str,
    title: str,
    url: str,
    location: str | None = None,
) -> None:
    """
    Send a Telegram message when a watchlisted company posts a new job.

    Safe to call even if Telegram is not configured — logs a warning
    instead of crashing the ingestion pipeline.
    """
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.debug(
            "telegram_alert_skipped",
            reason="bot_token or chat_id not configured",
            company=company,
        )
        return

    try:
        from telegram import Bot

        loc_str = f"\n📍 {location}" if location else ""
        message = (
            f"🚨 *Watchlist Hit!*\n"
            f"🏢 *{company}*\n"
            f"💼 {title}"
            f"{loc_str}\n"
            f"🔗 [Apply Now]({url})"
        )

        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        log.info(
            "telegram_alert_sent",
            company=company,
            title=title,
        )
    except Exception as e:
        # Never let Telegram failure crash the ingestion pipeline
        log.error(
            "telegram_alert_failed",
            error=str(e),
            company=company,
        )
