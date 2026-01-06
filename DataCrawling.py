from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd  # 엑셀 저장을 위한 라이브러리 추가

# 1. 브라우저 설정 (창을 띄우지 않으려면 headless 설정을 추가할 수 있습니다)
chrome_options = Options()
chrome_options.add_experimental_option("detach", True) # 브라우저 바로 꺼짐 방지

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

results = []

try:
    # 2. 페이지 접속
    url = "https://www.k-auction.com/Auction/Major/193"
    driver.get(url)
    
    # 3. 데이터가 로딩될 때까지 잠시 대기 (중요!)
    # 사이트가 정보를 불러올 시간을 3~5초 정도 줍니다.
    time.sleep(5)

    # 4. 작품 박스 찾기 (Selenium 방식)
    # 이미지에서 본 'div.col.mb-4'를 찾습니다.
    items = driver.find_elements(By.CSS_SELECTOR, 'div.col.mb-4')

    if not items:
        print("작품 리스트를 찾지 못했습니다. 대기 시간을 늘려보거나 클래스를 재확인하세요.")
    else:
        for item in items:
            try:
                # 데이터 추출
                artist = item.find_element(By.CSS_SELECTOR, '.card-title').text.strip()
                title = item.find_element(By.CSS_SELECTOR, '.card-text-subtitle').text.strip()
                img_element = item.find_element(By.CSS_SELECTOR,'.card-img-top')
                img_url = img_element.get_attribute('src')

                results.append({
                    "작가" : artist,
                    "작품명" : title,
                    "이미지주소" : img_url
                })
                print(f"추출 중: {artist} - {title}")
                
            except:
                continue

    if results:
        df = pd.DataFrame(results) # 추출된 리스트를 표(DataFrame) 형태로 변환
        df.to_excel(r"C:\Users\Gyun\OneDrive\Desktop\데이터크롤링\k_auction_list.xlsx", index=False) # 엑셀 파일로 저장
        print("\n" + "="*30)
        print("엑셀 파일 저장이 완료되었습니다: k_auction_list.xlsx")
        print("="*30)
finally:
    # 작업이 끝나면 브라우저 닫기 (원하면 주석 처리)
    # driver.quit()
    pass