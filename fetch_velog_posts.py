import requests
from bs4 import BeautifulSoup

# 벨로그 블로그 주소
BLOG_URL = "https://velog.io/@mypalebluedot29"

def fetch_recent_posts():
    response = requests.get(BLOG_URL)
    if response.status_code != 200:
        print("Failed to fetch the blog page.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 벨로그에서 최신 블로그 포스트 찾기
    post_elements = soup.select("div.sc-1db29b6-0.kmaMnt a")
    
    posts = []
    for post in post_elements[:5]:  # 최신 5개 글 가져오기
        title = post.text.strip()
        link = "https://velog.io" + post["href"]
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
        print("No new posts found.")
