from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# 벨로그 블로그 주소
BLOG_URL = "https://velog.io/@mypalebluedot29"

def fetch_recent_posts():
    # Selenium 설정
    options = Options()
    options.add_argument("--headless")  # GUI 없이 실행
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # 크롬 드라이버 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 벨로그 접속
    driver.get(BLOG_URL)
    time.sleep(5)  # 페이지가 완전히 로드될 때까지 대기
    
    # HTML 가져오기
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()  # 브라우저 종료

    # 최신 블로그 포스트 찾기
    post_elements = soup.select("div.FlatPostCard_block__a1qM7 > a.VLink_block__Uwj4P")  # 블로그 글 링크만 선택

    posts = []
    
    for post in post_elements:
        title_element = post.find("h2")

        # 제목이 없으면 제외
        if not title_element:
            continue
        
        title = title_element.text.strip()
        link = post["href"]
        
        # 상대 경로를 절대 경로로 변환
        if not link.startswith("https://"):
            link = "https://velog.io" + link

        # URL에 '#' 포함된 경우 제외 (해시태그 링크 필터링)
        if "#" in link:
            continue
        
        posts.append(f"- [{title}]({link})")
        
        # 최신 5개 글까지만 가져오기
        if len(posts) == 5:
            break
    
    return posts

# README.md 업데이트
def update_readme(posts):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.readlines()
    
    start_index = content.index("<!-- BLOG-POST-LIST:START -->\n") + 1
    end_index = content.index("<!-- BLOG-POST-LIST:END -->\n")
    
    new_content = content[:start_index] + posts + ["\n"] + content[end_index:]
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(new_content)

if __name__ == "__main__":
    recent_posts = fetch_recent_posts()
    if recent_posts:
        update_readme(recent_posts)
        print("✅ 최신 블로그 포스트 업데이트 완료!")
    else:
        print("❌ No new posts found. Check the blog URL or structure.")
