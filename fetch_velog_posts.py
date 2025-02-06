from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

# 벨로그 블로그 주소
BLOG_URL = "https://velog.io/@mypalebluedot29"

def fetch_recent_posts():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get(BLOG_URL)
    time.sleep(5)  
    driver.refresh()  # 최신 데이터 로드
    time.sleep(5)  

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()  

    post_elements = soup.select("div.FlatPostCard_block__a1qM7")

    posts = []
    
    for post in post_elements:
        a_tag = post.find("a", class_="VLink_block__Uwj4P")  
        h2_tag = post.find("h2")  
        date_spans = post.find_all("span") + post.find_all("p")  # ✅ <p> 태그도 확인

        if not a_tag or not h2_tag or not date_spans:
            continue  

        title = h2_tag.text.strip()
        link = a_tag["href"]

        # ✅ 상대 URL을 절대 URL로 변환
        if not link.startswith("https://"):
            link = "https://velog.io" + link

        raw_date = ""
        for element in date_spans:
            span_text = element.text.strip()
            if "전" in span_text or "어제" in span_text or re.match(r"\d{4}-\d{2}-\d{2}", span_text):
                raw_date = span_text
                break

        if not raw_date:
            continue  

        converted_date, sort_key = parse_relative_date(raw_date, return_sort_key=True)
        
        print(f"✅ 변환된 날짜: {converted_date}, 링크: {link} ({title})")  

        if not converted_date:
            continue

        posts.append((title, raw_date, converted_date, link, sort_key))
    
    # ✅ 최신순 정렬 (초 → 분 → 시간 → 어제 → 날짜)
    posts.sort(key=lambda x: x[4], reverse=True)

    return posts[:5]

import re
from datetime import datetime, timedelta

def parse_relative_date(date_str, return_sort_key=False):
    now = datetime.now()
    
    # ✅ "약 2시간 전", "대략 3분 전" 같은 표현에서 숫자만 추출
    numeric_value = re.sub(r"[^\d]", "", date_str)  # 숫자 이외의 모든 문자 제거
    if not numeric_value.isdigit():  # 숫자가 없으면 변환 실패
        return None if not return_sort_key else (None, None)
    
    numeric_value = int(numeric_value)  # 정수로 변환

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
            return None if not return_sort_key else (None, None)

    formatted_date = result_date.strftime("%Y-%m-%d %H:%M")

    return (formatted_date, sort_key) if return_sort_key else formatted_date
    
def update_readme(posts):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.readlines()
    
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
        "\n📅 **Last Updated:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (KST)\n",
        "🔗 **[📖 더 많은 글 보기](https://velog.io/@mypalebluedot29)**\n"
    ] + content[end_index:]

    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(new_content)

if __name__ == "__main__":
    recent_posts = fetch_recent_posts()
    if recent_posts:
        update_readme(recent_posts)
    else:
        print("❌ No new posts found. Check the blog URL or structure.")
