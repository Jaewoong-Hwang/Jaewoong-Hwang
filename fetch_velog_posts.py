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
        raw_date = date_span.text.strip()  # 원본 날짜 (상대적 표현 포함)

        # ✅ "어제"가 포함된 경우 로그 출력 (디버깅용)
        if "어제" in raw_date:
            print(f"❗ '어제' 발견: {title} - 원본 날짜: {raw_date}")

        # 상대 날짜 변환 (YYYY-MM-DD HH:MM 형식)
        date = parse_relative_date(raw_date)

        # ✅ 변환된 날짜 출력 확인 (디버깅용)
        print(f"📌 변환된 날짜: {date} - 제목: {title}")

        if not date:  # 변환된 날짜가 None이면 제외
            continue

        # 상대 경로를 절대 경로로 변환
        if not link.startswith("https://"):
            link = "https://velog.io" + link

        # URL에 '#' 포함된 경우 제외 (해시태그 링크 필터링)
        if "#" in link:
            continue
        
        posts.append((title, date, link))
    
    # 날짜 정렬 (최신순: 가장 최신 글이 위로 오도록)
    posts.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M"), reverse=True)

    return posts[:5]  # 최신 5개 게시물 반환
