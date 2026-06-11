import requests
import time
import logging
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from datetime import datetime

# ─── НАСТРОЙКИ ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8840732677:AAEkRf8CRJAszdDmm1vTtfVQVZ9fKMlkehc"
TELEGRAM_CHAT_ID = "5784107676"

# Gmail настройки
GMAIL_FROM = "miako.miko.kom@gmail.com"       # с какого адреса отправлять
GMAIL_PASSWORD = "iwzx gcsb cnpp ptgh"  # пароль приложения (не обычный пароль!)
GMAIL_TO = "miako.miko.kom@gmail.com"         # на какой адрес получать
 
URL = "https://iframeab-pre5088.intickets.ru/seance/72830766/"
CHECK_INTERVAL = 60
NO_TICKETS_PHRASE = "ВСЕ БИЛЕТЫ В БРОНИ ИЛИ РАСПРОДАНЫ"
MIN_PAGE_LENGTH = 1000
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
 
 
def send_gmail(subject: str, body: str) -> None:
    try:
        msg = MIMEText(body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = GMAIL_FROM
        msg["To"] = GMAIL_TO
 
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_FROM, GMAIL_PASSWORD)
            server.sendmail(GMAIL_FROM, GMAIL_TO, msg.as_string())
 
        logging.info("Gmail: письмо отправлено")
    except Exception as e:
        logging.error("Gmail send failed: %s", e)
 
 
def notify(subject: str, text_plain: str, text_html: str) -> None:
    """Отправляет уведомление сразу в Telegram и Gmail."""
    send_telegram(text_plain)
    send_gmail(subject, text_html)
 
 
def check_tickets() -> str:
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logging.warning("Ошибка запроса: %s", e)
        return "error"
 
    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(separator=" ")
    length = len(page_text.strip())
    logging.info("Длина страницы: %d символов", length)
 
    if length < MIN_PAGE_LENGTH:
        logging.warning("Страница слишком короткая — пропускаем")
        return "error"
 
    if NO_TICKETS_PHRASE in page_text.lower():
        return "no_tickets"
 
    if "₽" in page_text:
        return "available"
 
    logging.warning("Статус неизвестен, первые 300 символов: %s", page_text[:300])
    return "error"
 
 
def main():
    logging.info("Мониторинг запущен: %s", URL)
    notify(
        subject="🔍 Мониторинг билетов запущен",
        text_plain=(
            f"🔍 <b>Мониторинг запущен</b>\n"
            f"Слежу за билетами каждые {CHECK_INTERVAL} сек.\n"
            f"<a href='{URL}'>Открыть страницу</a>"
        ),
        text_html=(
            f"<h3>🔍 Мониторинг запущен</h3>"
            f"<p>Слежу за билетами каждые {CHECK_INTERVAL} сек.</p>"
            f"<p><a href='{URL}'>Открыть страницу</a></p>"
        ),
    )
 
    notified = False
 
    while True:
        status = check_tickets()
 
        if status == "available" and not notified:
            now = datetime.now().strftime("%H:%M:%S")
            notify(
                subject="🎟 БИЛЕТЫ ПОЯВИЛИСЬ!",
                text_plain=(
                    f"🎟 <b>БИЛЕТЫ ПОЯВИЛИСЬ!</b>\n"
                    f"⏰ {now}\n"
                    f"👉 <a href='{URL}'>Купить сейчас</a>"
                ),
                text_html=(
                    f"<h2>🎟 БИЛЕТЫ ПОЯВИЛИСЬ!</h2>"
                    f"<p>⏰ Время: {now}</p>"
                    f"<p><a href='{URL}' style='font-size:18px;color:green;'>"
                    f"👉 Купить сейчас</a></p>"
                ),
            )
            logging.info("✅ Билеты появились! Уведомления отправлены.")
            notified = True
 
        elif status == "no_tickets":
            logging.info("⏳ Билетов пока нет...")
            notified = False
 
        elif status == "error":
            logging.info("⚠️ Не удалось проверить страницу, пропускаем...")
 
        time.sleep(CHECK_INTERVAL)
 
 
if __name__ == "__main__":
    main()
 
