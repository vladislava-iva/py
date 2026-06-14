import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

# ─── НАСТРОЙКИ ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8840732677:AAEkRf8CRJAszdDmm1vTtfVQVZ9fKMlkehc"
TELEGRAM_CHAT_ID = "5784107676"

URL = "https://iframeab-pre5088.intickets.ru/seance/72830766/"
CHECK_INTERVAL = 8   # проверять каждые N секунд
NO_TICKETS_PHRASE = "ВСЕ БИЛЕТЫ В БРОНИ ИЛИ РАСПРОДАНЫ"
# ────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.ok:
            logging.info("Telegram: сообщение отправлено")
        else:
            logging.error("Telegram error: %s", resp.text)
    except Exception as e:
        logging.error("Telegram send failed: %s", e)


def check_tickets(page) -> str:
    try:
        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        content = page.inner_text("body")
    except Exception as e:
        logging.warning("Ошибка загрузки страницы: %s", e)
        return "error"

    logging.info("Длина страницы: %d символов", len(content.strip()))

    if len(content.strip()) < 500:
        logging.warning("Страница слишком короткая — пропускаем")
        return "error"

    if NO_TICKETS_PHRASE.lower() in content.lower():
        return "no_tickets"

    if "₽" in content:
        return "available"

    logging.warning("Статус непонятен")
    return "error"

def main():
    logging.info("Мониторинг запущен: %s", URL)
    send_telegram(
        f"🔍 <b>Мониторинг запущен</b>\n"
        f"Слежу за билетами каждые {CHECK_INTERVAL} сек.\n"
        f"<a href='{URL}'>Открыть страницу</a>"
    )

    notified = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )
        page = context.new_page()

        try:
            while True:
                status = check_tickets(page)

                if status == "available" and not notified:
                    msg = (
                        f"🎟 <b>БИЛЕТЫ ПОЯВИЛИСЬ!</b>\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
                        f"👉 <a href='{URL}'>Купить сейчас</a>"
                    )
                    send_telegram(msg)
                    logging.info("✅ Билеты появились!")
                    notified = True

                elif status == "no_tickets":
                    logging.info("⏳ Билетов пока нет...")
                    notified = False

                elif status == "error":
                    logging.info("⚠️ Не удалось проверить, пропускаем...")

                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logging.info("Остановлено пользователем")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
