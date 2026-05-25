import os
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

        msg = f"""
🎬 新影片更新

{title}

✅ 已出现磁力链接

📎 磁力：
{magnet}

🔗 页面：
{full_link}
"""

        if cover:
            send_photo(msg, cover)

        seen[actress_url] = full_link

    except Exception as e:
        print(e)

with open(SEEN_FILE, "w", encoding="utf-8") as f:
    json.dump(seen, f, ensure_ascii=False, indent=2)
