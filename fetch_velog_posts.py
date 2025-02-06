from datetime import datetime, timedelta

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
        date_spans = post.find_all("span")  

        if not a_tag or not h2_tag or not date_spans:
            continue  

        title = h2_tag.text.strip()
        link = a_tag["href"]
        
        raw_date = ""
        for span in date_spans:
            span_text = span.text.strip()
            if "전" in span_text or "어제" in span_text or re.match(r"\d{4}-\d{2}-\d{2}", span_text):
                raw_date = span_text
                break

        if not raw_date:
            continue  

        # ✅ 상대 시간을 정렬할 수 있도록 숫자로 변환
        converted_date, sort_key = parse_relative_date(raw_date, return_sort_key=True)
        
        print(f"✅ 변환된 날짜: {converted_date}, 정렬 값: {sort_key} ({title})")  

        if not converted_date:
            continue

        if not link.startswith("https://"):
            link = "https://velog.io" + link

        posts.append((title, raw_date, converted_date, link, sort_key))
    
    # ✅ 초 → 분 → 시간 → 어제 → 날짜 순으로 정렬
    posts.sort(key=lambda x: x[4], reverse=True)

    return posts[:5]

def parse_relative_date(date_str, return_sort_key=False):
    now = datetime.now()
    
    if "초 전" in date_str:
        seconds = int(date_str.replace("초 전", "").strip())
        result_date = now - timedelta(seconds=seconds)
        sort_key = 1000000 - seconds  # 높은 숫자가 최신 순

    elif "분 전" in date_str:
        minutes = int(date_str.replace("분 전", "").strip())
        result_date = now - timedelta(minutes=minutes)
        sort_key = 900000 - minutes  # 초보다 작은 값

    elif "시간 전" in date_str:
        hours = int(date_str.replace("시간 전", "").strip())
        result_date = now - timedelta(hours=hours)
        sort_key = 800000 - hours  # 분보다 작은 값

    elif "어제" in date_str:
        result_date = now - timedelta(days=1)
        sort_key = 700000  # "어제"는 상대적으로 낮은 값

    else:
        try:
            result_date = datetime.strptime(date_str, "%Y-%m-%d")
            sort_key = int(result_date.strftime("%Y%m%d"))  # 날짜 값 자체를 정렬 기준으로 사용
        except ValueError:
            return None if not return_sort_key else (None, None)

    formatted_date = result_date.strftime("%Y-%m-%d %H:%M")

    return (formatted_date, sort_key) if return_sort_key else formatted_date

