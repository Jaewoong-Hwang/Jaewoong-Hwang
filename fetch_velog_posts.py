from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta

# 벨로그 블로그 주소
BLOG_URL = "https://velog.io/@mypalebluedot29"

def parse_relative_date(relative_date):
    """
    '11분 전', '1시간 전', '어제' 같은 상대적인 날짜를 변환하여 yyyy-mm-dd 형식으로 반환
    """
    now = datetime.now()

    if "분 전" in relative_date:
        minutes = int(relative_date.replace("분 전", "").strip())
        return (now - timedelta(minutes=minutes)).strftime("%Y-%m-%d")

    elif "시간 전" in relative_date:
        hours = int(relative_date.replace("시간 전", "").strip())
        return (now - timedelta(hours=hours)).strftime("%Y-%m-%d")

    elif "어제" in relative_date:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    else:
        return relative_date  # 원래 날짜 포맷을 유지

def fetch_recent_posts():
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get(BLOG_URL)
    time.sleep(5)  
    driver.refresh()  # 강제 새로고침 (최신 데이터 로드)
    time.sleep(5)  

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()  

    # 블로그 포스트 컨테이너 선택
    post_elements = soup.select("div.FlatPostCard_block__a1qM7")

    posts = []
    
    for post in post_elements:
        a_tag = post.find("a", class_="VLink_block__Uwj4P")  # 블로그 링크 찾기
        h2_tag = post.find("h2")  # 제목 찾기
        date_span = post.find("span")  # 작성일 찾기

        if not a_tag or not h2_tag or not date_span:
            continue  # 하나라도 없으면 건너뜀

        title = h2_tag.text.strip()  # 블로그 제목
        link = a_tag["href"]  # 블로그 URL
        raw_date = date_span.text.strip()  # 원본 날짜

        # 상대 날짜 변환
        date = parse_relative_date(raw_date)

        # 상대 경로를 절대 경로로 변환
        if not link.startswith("https://"):
            link = "https://velog.io" + link

        # URL에 '#' 포함된 경우 제외 (해시태그 링크 필터링)
        if "#" in link:
            continue
        
        posts.append((title, date, link))
        
        # 최신 5개 글까지만 가져오기
        if len(posts) == 5:
            break
    
    return posts


def format_blog_posts(posts):
    """
    블로그 글을 Markdown 표 형식으로 변환
    """
    markdown_content = "## 📝 Latest Blog Posts\n> 벨로그에서 최신 블로그 글을 자동 업데이트합니다! 🚀\n\n"
    markdown_content += "| 📝 제목 | 📅 작성일 | 🔗 링크 |\n"
    markdown_content += "|---------|------------|---------|\n"
    for title, date, link in posts:
        markdown_content += f"| **{title}** | {date} | [바로가기]({link}) |\n"
    
    markdown_content += "\n🔗 **[📖 더 많은 글 보기](https://velog.io/@mypalebluedot29)**\n"
    
    return markdown_content

ddef update_readme(posts):
    """
    README.md 파일을 업데이트하여 최신 블로그 글을 추가
    """
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.readlines()
    
    # README에 해당 섹션이 없으면 추가
    if "<!-- BLOG-POST-LIST:START -->\n" not in content:
        content.append("\n## 📝 Latest Blog Posts\n")
        content.append("> 벨로그에서 최신 블로그 글을 자동 업데이트합니다! 🚀\n\n")
        content.append("<!-- BLOG-POST-LIST:START -->\n")
        content.append("<!-- BLOG-POST-LIST:END -->\n")

    start_index = content.index("<!-- BLOG-POST-LIST:START -->\n") + 1
    end_index = content.index("<!-- BLOG-POST-LIST:END -->\n")

    # 현재 날짜 추가
    last_updated = f"\n📅 **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (KST)\n\n"

    new_content = content[:start_index] + [format_blog_posts(posts)] + [last_updated] + content[end_index:]

    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(new_content)


if __name__ == "__main__":
    recent_posts = fetch_recent_posts()
    if recent_posts:
        update_readme(recent_posts)
        print("✅ 최신 블로그 포스트 업데이트 완료!")
    else:
        print("❌ No new posts found. Check the blog URL or structure.")
