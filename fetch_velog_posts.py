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

# ✅ 상대 날짜 변환 함수
def parse_relative_date(date_str, return_sort_key=False):
    now = datetime.now()

    # ✅ "약 2시간 전" 같은 표현에서 숫자만 추출
    numeric_value = re.sub(r"[^\d]", "", date_str)
    if not numeric_value.isdigit():
        return now.strftime("%Y-%m-%d %H:%M"), int(now.strftime("%Y%m%d%H%M"))

    numeric_value = int(numeric_value)

    if "초 전" in date_str:
        result_date = now - timedelta(seconds=numeric_value)
        sort_key = 1000000 - numeric_value

    elif "분 전" in date_str:
        result_date = now - timedelta(minutes=numeric_value)
        sort_key = 900000 - numeric_value

    elif "시간 전" in date_str:
        result_date = now - timedelta(hours=numeric_value)
        sort_key = 800000 - numeric_value

    elif "어제" in date_str:
        result_date = now - timedelta(days=1)
        sort_key = 700000

    else:
        try:
            result_date = datetime.strptime(date_str, "%Y-%m-%d")
            sort_key = int(result_date.strftime("%Y%m%d"))
        except ValueError:
            return now.strftime("%Y-%m-%d %H:%M"), int(now.strftime("%Y%m%d%H%M"))

    formatted_date = result_date.strftime("%Y-%m-%d %H:%M")
    return (formatted_date, sort_key) if return_sort_key else formatted_date


# ✅ 블로그 크롤링 함수
def fetch_recent_posts():
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
        raw_date, sort_key = datetime.now().strftime("%Y-%m-%d %H:%M"), int(datetime.now().strftime("%Y%m%d%H%M"))

        for element in date_spans:
            span_text = element.text.strip()
            if "전" in span_text or "어제" in span_text or re.match(r"\d{4}-\d{2}-\d{2}", span_text):
                parsed_date = parse_relative_date(span_text, return_sort_key=True)
                if parsed_date:
                    raw_date, sort_key = parsed_date
                break

        print(f"✅ 변환된 날짜: {raw_date}, 링크: {link} ({title})")

        posts.append((title, raw_date, raw_date, link, sort_key))

    # ✅ 최신순 정렬 (초 → 분 → 시간 → 어제 → 날짜)
    posts.sort(key=lambda x: x[4], reverse=True)

    # ✅ 항상 5개 유지
    return posts[:5] if len(posts) >= 5 else posts


# ✅ README 업데이트 함수
def update_readme(posts):
    try:
        # ✅ README.md 파일이 없을 경우 생성
        if not os.path.exists("README.md"):
            print("⚠️ README.md 파일이 없어 새로 생성합니다.")
            with open("README.md", "w", encoding="utf-8") as f:
                f.write("# 📌 My GitHub Profile\n\n")

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

        new_content = content[:start_index] + [
            "| 📝 제목 | 📅 작성일 (상대/변환) | 🔗 링크 |\n",
            "|---------|------------------|---------|\n",
        ] + [
            f"| **{title}** | {original_date} ({converted_date}) | [바로가기]({link}) |\n"
            if original_date != converted_date else f"| **{title}** | {converted_date} | [바로가기]({link}) |\n"
            for title, original_date, converted_date, link, _ in posts
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
