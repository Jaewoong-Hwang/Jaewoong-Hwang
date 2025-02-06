from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

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
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()  

    post_elements = soup.select("div.FlatPostCard_block__a1qM7 > a.VLink_block__Uwj4P")  

    posts = []
    
    for post in post_elements:
        title_element = post.find("h2")
        if not title_element:
            continue
        
        title = title_element.text.strip()
        link = post["href"]
        if not link.startswith("https://"):
            link = "https://velog.io" + link

        if "#" in link:
            continue
        
        date_element = post.find_next("span")  
        date = date_element.text.strip() if date_element else "Unknown Date"

        posts.append((title, date, link))
        
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

def update_readme(posts):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.readlines()
    
    # 주석이 없을 경우 자동 추가
    if "<!-- BLOG-POST-LIST:START -->\n" not in content:
        content.append("\n## 📝 Latest Blog Posts\n")
        content.append("> 벨로그에서 최신 블로그 글을 자동 업데이트합니다! 🚀\n\n")
        content.append("<!-- BLOG-POST-LIST:START -->\n")
        content.append("<!-- BLOG-POST-LIST:END -->\n")

    start_index = content.index("<!-- BLOG-POST-LIST:START -->\n") + 1
    end_index = content.index("<!-- BLOG-POST-LIST:END -->\n")
    
    new_content = content[:start_index] + [format_blog_posts(posts)] + content[end_index:]
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(new_content)
