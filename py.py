import requests
import time
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# ─── НАСТРОЙКИ ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8840732677:AAEkRf8CRJAszdDmm1vTtfVQVZ9fKMlkehc"       # от @BotFather
TELEGRAM_CHAT_ID = "5784107676"        # твой числовой ID

URL = "https://iframeab-pre5088.intickets.ru/seance/72830766/"
CHECK_INTERVAL = 60   # проверять каждые N секунд (60 = раз в минуту)
# ────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://google.com",
}

# Фраза, которая означает «билетов нет»
NO_TICKETS_PHRASES = [
    "ВСЕ БИЛЕТЫ В БРОНИ ИЛИ РАСПРОДАНЫ",
]


def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            logging.error("Telegram error: %s", resp.text)
    except Exception as e:
        logging.error("Telegram send failed: %s", e)


def check_tickets() -> bool:
    """Возвращает True, если билеты ПОЯВИЛИСЬ (недоступность НЕ обнаружена)."""
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logging.warning("Ошибка запроса: %s", e)
        return False

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(separator=" ").lower()

    # Если на странице есть хоть одна фраза «нет билетов» — всё ещё пусто
    for phrase in NO_TICKETS_PHRASES:
        if phrase in page_text:
            return False

    # Дополнительно ищем кнопку/ссылку покупки
    buy_keywords = ["купить", "buy", "добавить в корзину", "order", "заказать"]
    for kw in buy_keywords:
        if kw in page_text:
            return True

    # Если фраз «нет билетов» нет и страница загрузилась — считаем, что появились
    return True


def main():
    logging.info("Мониторинг запущен: %s", URL)
    send_telegram(
        f"🔍 <b>Мониторинг запущен</b>\n"
        f"Слежу за билетами каждые {CHECK_INTERVAL} сек.\n"
        f"<a href='{URL}'>Открыть страницу</a>"
    )

    notified = False

    while True:
        available = check_tickets()
        now = datetime.now().strftime("%H:%M:%S")

        if available and not notified:
            msg = (
                f"🎟 <b>БИЛЕТЫ ПОЯВИЛИСЬ!</b>\n"
                f"⏰ {now}\n"
                f"👉 <a href='{URL}'>Купить сейчас</a>"
            )
            send_telegram(msg)
            logging.info("✅ Билеты появились! Уведомление отправлено.")
            notified = True  # не спамим повторно

        elif not available:
            logging.info("⏳ Билетов пока нет...")
            notified = False  # сбрасываем флаг, если снова пропали

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()