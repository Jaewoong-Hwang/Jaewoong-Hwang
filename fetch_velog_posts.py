from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
import os

# 벨로그 블로그 주소
BLOG_URL = "https://velog.io/@mypalebluedot29"


def parse_relative_date(date_str, return_sort_key=False):
    """ 상대적인 날짜 (n분 전, n시간 전, n일 전, 어제)와 절대적인 날짜 (YYYY년 M월 D일)를 변환 """
    now = datetime.now()

    # ✅ "YYYY년 M월 D일" 형식 처리
    date_match = re.search(r"(\d{4})년 (\d{1,2})월 (\d{1,2})일", date_str)
    if date_match:
        year, month, day = date_match.groups()
        parsed_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"  # `YYYY-MM-DD` 변환
        sort_key = int(f"{year}{month.zfill(2)}{day.zfill(2)}0000")  # 정렬용 키
        return (parsed_date, sort_key) if return_sort_key else parsed_date

    # ✅ "n일 전" 처리
    days_match = re.search(r"(\d+)일 전", date_str)
    if days_match:
        days_ago = int(days_match.group(1))
        parsed_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        sort_key = int((now - timedelta(days=days_ago)).strftime("%Y%m%d%H%M"))
        return (parsed_date, sort_key) if return_sort_key else parsed_date

    # ✅ "n시간 전" 처리
    hours_match = re.search(r"(\d+)시간 전", date_str)
    if hours_match:
        hours_ago = int(hours_match.group(1))
        adjusted_time = now - timedelta(hours=hours_ago)
        parsed_date = adjusted_time.strftime("%Y-%m-%d")  # 오늘인지 어제인지 판단
        sort_key = int(adjusted_time.strftime("%Y%m%d%H%M"))
        return (parsed_date, sort_key) if return_sort_key else parsed_date

    # ✅ "n분 전" 처리
    minutes_match = re.search(r"(\d+)분 전", date_str)
    if minutes_match:
        minutes_ago = int(minutes_match.group(1))
        adjusted_time = now - timedelta(minutes=minutes_ago)
        parsed_date = adjusted_time.strftime("%Y-%m-%d")  # 오늘인지 어제인지 판단
        sort_key = int(adjusted_time.strftime("%Y%m%d%H%M"))
        return (parsed_date, sort_key) if return_sort_key else parsed_date

    # ✅ "어제" 처리
    if "어제" in date_str:
        parsed_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        sort_key = int((now - timedelta(days=1)).strftime("%Y%m%d%H%M"))
        return (parsed_date, sort_key) if return_sort_key else parsed_date

    # ✅ 기본값 (오늘 날짜)
    parsed_date = now.strftime("%Y-%m-%d")
    sort_key = int(now.strftime("%Y%m%d%H%M"))
    return (parsed_date, sort_key) if return_sort_key else parsed_date


def fetch_recent_posts():
    """ 벨로그에서 최신 블로그 게시물을 크롤링하여 반환 """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(BLOG_URL)
    time.sleep(5)
    driver.refresh()
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    post_elements = soup.select("div.FlatPostCard_block__a1qM7")
    posts = []

    for post in post_elements:
        a_tag = post.find("a", class_="VLink_block__Uwj4P")
        h2_tag = post.find("h2")
        date_spans = post.find_all("span") + post.find_all("p")

        if not a_tag or not h2_tag:
            continue

        title = h2_tag.text.strip()
        link = a_tag["href"]

        # ✅ 상대 URL을 절대 URL로 변환
        if not link.startswith("https://"):
            link = "https://velog.io" + link

        # ✅ 기본값 설정 (날짜가 없을 경우 대비)
        raw_date, sort_key = datetime.now().strftime("%Y-%m-%d"), int(datetime.now().strftime("%Y%m%d%H%M"))

        for element in date_spans:
            span_text = element.text.strip()
            if "전" in span_text or "어제" in span_text or re.search(r"\d{4}년 \d{1,2}월 \d{1,2}일", span_text):
                parsed_date, parsed_sort_key = parse_relative_date(span_text, return_sort_key=True)
                raw_date, sort_key = parsed_date, parsed_sort_key
                break

        print(f"✅ 변환된 날짜: {raw_date}, 링크: {link} ({title})")

        posts.append((title, raw_date, raw_date, link, sort_key))

    # ✅ 최신순 정렬
    posts.sort(key=lambda x: x[4], reverse=True)

    # ✅ 항상 5개 유지
    return posts[:5] if len(posts) >= 5 else posts


def update_readme(posts):
    """ README.md 파일을 업데이트하여 최신 블로그 포스트를 반영 """
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.readlines()

        try:
            start_index = content.index("<!-- BLOG-POST-LIST:START -->\n") + 1
            end_index = content.index("<!-- BLOG-POST-LIST:END -->\n")
        except ValueError:
            print("⚠️ README.md에 자동 업데이트 영역이 없어 새로 추가합니다.")
            content.append("\n## 📝 Latest Blog Posts\n")
            content.append("<!-- BLOG-POST-LIST:START -->\n")
            content.append("<!-- BLOG-POST-LIST:END -->\n")
            start_index = content.index("<!-- BLOG-POST-LIST:START -->\n") + 1
            end_index = content.index("<!-- BLOG-POST-LIST:END -->\n")

        # ✅ 최신 블로그 글을 표 형식으로 업데이트
        new_content = content[:start_index] + [
            "| 📝 제목 | 📅 작성일 | 🔗 링크 |\n",
            "|---------|------------------|---------|\n",
        ] + [
            f"| **{title}** | {converted_date} | [바로가기]({link}) |\n"
            for title, _, converted_date, link, _ in posts
        ] + [
            "\n📅 **Last Updated:** " + datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S") + " (KST)\n",
            "🔗 **[📖 더 많은 글 보기](https://velog.io/@mypalebluedot29)**\n"
        ] + content[end_index:]

        if "".join(content) != "".join(new_content):
            with open("README.md", "w", encoding="utf-8") as f:
                f.writelines(new_content)
            print("✅ README.md 업데이트 완료!")
        else:
            print("ℹ️ 변경 사항이 없어 업데이트하지 않음.")

    except Exception as e:
        print(f"❌ README 업데이트 중 오류 발생: {e}")


if __name__ == "__main__":
    recent_posts = fetch_recent_posts()
    if recent_posts:
        update_readme(recent_posts)
