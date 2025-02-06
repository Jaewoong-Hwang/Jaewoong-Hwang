import requests
from bs4 import BeautifulSoup

# 벨로그 블로그 주소
BLOG_URL = "https://velog.io/@mypalebluedot29"

def fetch_recent_posts():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
    }
    response = requests.get(BLOG_URL, headers=headers)
    
    if response.status_code != 200:
        print("❌ Failed to fetch the blog page.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")

    # 최신 블로그 글 요소 선택
    post_elements = soup.select("a.VLink_block__Uwj4P")

    posts = []
    for post in post_elements[:5]:  # 최신 5개 글 가져오기
        link = post["href"]
        title_element = post.find("h2")  # 제목 찾기
        title = title_element.text.strip() if title_element else "Untitled"
        posts.append(f"- [{title}]({link})")
    
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
    else:
        print("❌ No new posts found. Check the blog URL or structure.")
