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

# 读取已推送记录
if os.path.exists(SEEN_FILE):

    with open(SEEN_FILE, "r", encoding="utf-8") as f:

        seen = json.load(f)

else:

    seen = {}

# 每日合集
if os.path.exists(DAILY_FILE):

    with open(DAILY_FILE, "r", encoding="utf-8") as f:

        daily = json.load(f)

else:

    daily = {}

today = datetime.now().strftime("%Y-%m-%d")

if today not in daily:

    daily = {today: []}


# Telegram 图片消息
def send_photo(caption, photo_url, magnet, page_url):

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📎 Magnet",
                    "url": magnet
                },
                {
                    "text": "🔗 页面",
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


# Telegram 纯文本消息
def send_message(text):

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


# 读取 actresses.txt
with open("actresses.txt", "r", encoding="utf-8") as f:

    actress_lines = [x.strip() for x in f.readlines() if x.strip()]


# 开始循环
for line in actress_lines:

    try:

        # 支持 名字 | 链接
        if "|" in line:

            parts = line.split("|")

            actress_name = parts[0].strip()

            actress_url = parts[1].strip()

        else:

            actress_name = "未知演员"

            actress_url = line.strip()

        # 打开演员页面
        html = scraper.get(actress_url, headers=HEADERS).text

        soup = BeautifulSoup(html, "lxml")

        # 自动读取演员名字
        if actress_name == "未知演员":

            try:

                title_tag = soup.select_one("h2.title")

                if title_tag:

                    actress_name = title_tag.get_text(strip=True)

            except:
                pass

        cards = soup.select(".movie-list .item")

        if not cards:
            continue

        # 检查最近5部
        latest_cards = cards[:5]

        for latest in latest_cards:

            try:

                link = latest.find("a")["href"]

                full_link = "https://javdb.com" + link

                # 去重
                if full_link in seen:
                    continue

                title = latest.get_text(" ", strip=True)

                # 提取番号
                code_match = re.search(r"[A-Z]{2,10}-\d+", title)

                code = code_match.group(0) if code_match else "未知番号"

                # 打开影片页
                video_html = scraper.get(full_link, headers=HEADERS).text

                # 没 magnet 跳过
                if "magnet:?" not in video_html:
                    continue

                video_soup = BeautifulSoup(video_html, "lxml")

                # 封面
                img = video_soup.select_one(".video-cover img")

                cover = ""

                if img:

                    cover = img.get("src", "")

                # magnet
                magnet = ""

                magnets = video_soup.select("a")

                for m in magnets:

                    href = m.get("href", "")

                    if href.startswith("magnet:?"):

                        magnet = href

                        break

                # 最近4部
                other_titles = []

                for other in latest_cards[1:5]:

                    try:

                        other_title = other.get_text(" ", strip=True)

                        other_match = re.search(
                            r"[A-Z]{2,10}-\d+",
                            other_title
                        )

                        other_code = (
                            other_match.group(0)
                            if other_match
                            else "未知"
                        )

                        other_titles.append(
                            f"• {other_code}"
                        )

                    except:
                        pass

                other_text = "\n".join(other_titles)

                # 推送内容
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

                # 发送
                if cover and magnet:

                    send_photo(
                        msg,
                        cover,
                        magnet,
                        full_link
                    )

                # 标记已推送
                seen[full_link] = True

                # 每日合集
                daily[today].append(
                    f"{actress_name} - {code}"
                )

            except Exception as e:

                print(e)

    except Exception as e:

        print(e)


# 每日合集
today_items = daily.get(today, [])

if today_items:

    summary = f"📅 今日更新合集 ({today})\n\n"

    for item in today_items:

        summary += f"• {item}\n"

    send_message(summary)


# 保存 seen
with open(SEEN_FILE, "w", encoding="utf-8") as f:

    json.dump(
        seen,
        f,
        ensure_ascii=False,
        indent=2
    )


# 保存 daily
with open(DAILY_FILE, "w", encoding="utf-8") as f:

    json.dump(
        daily,
        f,
        ensure_ascii=False,
        indent=2
    )
