import os
import re
import json
import requests
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

scraper = cloudscraper.create_scraper()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SEEN_FILE = "seen.json"
DAILY_FILE = "daily.json"

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        seen = json.load(f)
else:
    seen = {}

if os.path.exists(DAILY_FILE):
    with open(DAILY_FILE, "r", encoding="utf-8") as f:
        daily = json.load(f)
else:
    daily = {}

today = datetime.now().strftime("%Y-%m-%d")

if today not in daily:
    daily = {today: []}


def send_photo(caption, photo_url, magnet, page_url):

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📎 复制 Magnet",
                    "url": magnet
                },
                {
                    "text": "🔗 打开页面",
                    "url": page_url
                }
            ]
        ]
    }

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "caption": caption,
            "photo": photo_url,
            "reply_markup": json.dumps(keyboard)
        }
    )


def send_message(text):

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


with open("actresses.txt", "r", encoding="utf-8") as f:
    actress_lines = [x.strip() for x in f.readlines() if x.strip()]


for line in actress_lines:

    try:

        actress_name, actress_url = line.split("|")

        actress_name = actress_name.strip()

        actress_url = actress_url.strip()

        html = scraper.get(actress_url, headers=HEADERS).text

        soup = BeautifulSoup(html, "lxml")

        cards = soup.select(".movie-list .item")

        if not cards:
            continue

        latest_cards = cards[:5]

        for latest in latest_cards:

            link = latest.find("a")["href"]

            full_link = "https://javdb.com" + link

            if full_link in seen:
                continue

            title = latest.get_text(" ", strip=True)

            code_match = re.search(r"[A-Z]{2,10}-\d+", title)

            code = code_match.group(0) if code_match else "未知番号"

            video_html = scraper.get(full_link, headers=HEADERS).text

            if "magnet:?" not in video_html:
                continue

            video_soup = BeautifulSoup(video_html, "lxml")

            img = video_soup.select_one(".video-cover img")

            cover = ""

            if img:
                cover = img.get("src", "")

            magnet = ""

            magnets = video_soup.select("a")

            for m in magnets:

                href = m.get("href", "")

                if href.startswith("magnet:?"):

                    magnet = href

                    break

            other_titles = []

            for other in latest_cards[1:5]:

                try:

                    other_title = other.get_text(" ", strip=True)

                    other_match = re.search(r"[A-Z]{2,10}-\d+", other_title)

                    other_code = other_match.group(0) if other_match else "未知"

                    other_titles.append(f"• {other_code}")

                except:
                    pass

            other_text = "\n".join(other_titles)

            msg = f"""
🎬 新影片更新

👩 演员：
{actress_name}

🎞 番号：
{code}

✅ 已出现磁力链接

📚 最近影片：
{other_text}

"""

            if cover and magnet:

                send_photo(
                    msg,
                    cover,
                    magnet,
                    full_link
                )

            seen[full_link] = True

            daily[today].append(
                f"{actress_name} - {code}"
            )

    except Exception as e:

        print(e)

summary = f"📅 今日更新合集 ({today})\n\n"

today_items = daily.get(today, [])

if today_items:

    for item in today_items:

        summary += f"• {item}\n"

    send_message(summary)

with open(SEEN_FILE, "w", encoding="utf-8") as f:

    json.dump(seen, f, ensure_ascii=False, indent=2)

with open(DAILY_FILE, "w", encoding="utf-8") as f:

    json.dump(daily, f, ensure_ascii=False, indent=2)
