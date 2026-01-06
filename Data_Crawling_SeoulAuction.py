from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import datetime
import streamlit as st

# 웹 페이지 제목 설정
st.title("🏛️ 서울옥션 데이터 수집기")
st.write("버튼을 누르면 실시간으로 데이터를 수집하여 엑셀로 만들어줍니다.")

# 1. 브라우저 설정
cchrome_options = Options()
chrome_options.add_argument("--headless") # 화면 없이 실행 (필수)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

results = []

try:
    # 2. 서울옥션 프라이빗 세일 페이지 접속
    url = "https://www.seoulauction.com/privatesale/psList"
    driver.get(url)
    
    # 3. 데이터 로딩 대기 (서울옥션은 로딩이 다소 걸릴 수 있어 7초로 설정)
    time.sleep(7)

    # 4. 작품 리스트 찾기
    # 서울옥션의 각 작품 카드는 'div.list_item' 구조를 가지고 있습니다.
    items = driver.find_elements(By.CSS_SELECTOR, 'div.li-inner')

    if not items:
        print("작품 리스트를 찾지 못했습니다. 페이지 로딩 상태를 확인하세요.")
    else:
        for item in items:
            try:
                # 기본 정보 추출
                brand = item.find_element(By.CSS_SELECTOR, '.info-box .title span').text.strip()
                product_name = item.find_element(By.CSS_SELECTOR, '.info-box .desc span').text.strip()
                
                # 이미지 주소 추출
                img_url = item.find_element(By.CSS_SELECTOR, '.img-align img').get_attribute('src')

                # --- 데이터가 없을 수도 있는 항목들 처리 ---
                
                # 소재 추출
                try:
                    material = item.find_element(By.CSS_SELECTOR, '.text-over .txt-material').text.strip()
                except:
                    material = "소재 정보 없음"

                # 사이즈 추출
                try:
                    # 요소가 존재하는지 먼저 확인
                    size_element = item.find_elements(By.CSS_SELECTOR, '.size_year')
                    if size_element:
                        product_size = size_element[0].text.strip()
                    else:
                        product_size = "-" # 정보가 없을 경우 표시할 내용
                except:
                    product_size = "-"

                # 리스트에 담기
                results.append({
                    "브랜드": brand,
                    "제품명": product_name,
                    "소재": material,
                    "사이즈": product_size,
                    "이미지주소": img_url
                })
                print(f"추출 성공: {brand} - {product_name} (사이즈: {product_size})")
                
            except Exception as e:
                continue
    
    # # 5. 엑셀 저장
    if results:
        df = pd.DataFrame(results)
        file_name = "seoul_auction_private.xlsx"
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"seoul_auction_{now}.xlsx"
        df.to_excel(file_name, index=False)
        print("\n" + "="*30)
        print(f"저장 완료: {file_name}")
        print("="*30)
    
finally:
    # driver.quit() # 확인을 위해 브라우저를 열어두려면 주석 처리
    pass