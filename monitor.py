import os
import json
import requests
import cloudscraper
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

scraper = cloudscraper.create_scraper()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SEEN_FILE = "seen.json"

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        seen = json.load(f)
else:
    seen = {}

def send_photo(caption, photo_url):

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "caption": caption,
            "photo": photo_url
        }
    )
send_photo(
    "✅ 测试成功，你的 Telegram 推送正常",
    "https://picsum.photos/400/600"
)
with open("actresses.txt", "r", encoding="utf-8") as f:
    actress_urls = [x.strip() for x in f.readlines() if x.strip()]

for actress_url in actress_urls:

    try:

        html = scraper.get(actress_url, headers=HEADERS).text

        soup = BeautifulSoup(html, "lxml")

        cards = soup.select(".movie-list .item")

        if not cards:
            continue

        latest = cards[0]

        link = latest.find("a")["href"]

        full_link = "https://javdb.com" + link

        title = latest.get_text(strip=True)

        if actress_url in seen and seen[actress_url] == full_link:
            continue

        video_html = scraper.get(full_link, headers=HEADERS).text

        if "magnet" not in video_html.lower():
            continue

        video_soup = BeautifulSoup(video_html, "lxml")

        img = video_soup.select_one(".video-cover img")

        cover = ""

        if img:
            cover = img.get("src", "")

        magnet = "未找到"

        magnets = video_soup.select("a")

        for m in magnets:

            href = m.get("href", "")

            if href.startswith("magnet:?"):
                magnet = href
                break

        msg = f'''
🎬 新影片更新

{title}

✅ 已出现磁力链接

📎 磁力：
{magnet}

🔗 页面：
{full_link}
'''

        if cover:
            send_photo(msg, cover)

        seen[actress_url] = full_link

    except Exception as e:
        print(e)

with open(SEEN_FILE, "w", encoding="utf-8") as f:
    json.dump(seen, f, ensure_ascii=False, indent=2)
