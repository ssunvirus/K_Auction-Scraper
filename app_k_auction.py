import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import pandas as pd
import datetime
import io

# 1. 페이지 설정
st.set_page_config(page_title="케이옥션 통합 수집기", page_icon="🎨")
st.title("📚 케이옥션 회차별 전 페이지 수집기")

# --- UI 설정 ---
st.sidebar.header("🔍 수집 범위 설정")
start_no = st.sidebar.number_input("시작 회차 번호", min_value=1, value=193)
end_no = st.sidebar.number_input("종료 회차 번호", min_value=1, value=193)

if st.button("🚀 전체 데이터 수집 시작"):
    all_results = []
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    try:
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        for auction_no in range(start_no, end_no + 1):
            page_idx = 1
            while True: # 페이지 번호를 1부터 하나씩 늘리며 반복
                target_url = f"https://www.k-auction.com/Auction/Major/{auction_no}?page_size=100&page={page_idx}"
                st.write(f"🔄 제 {auction_no}회 - {page_idx}페이지 수집 중...")
                
                driver.get(target_url)
                time.sleep(10) # 서버 부하 방지 및 로딩 대기

                items = driver.find_elements(By.CSS_SELECTOR, 'div.col.mb-4.list-pd.major-list-pd')
                
                # 해당 페이지에 작품이 없으면 해당 회차 수집 종료
                if not items or len(items) <= 0:
                    break

                for item in items:
                    try:
                        if "card-empty" in item.get_attribute("class"): continue
                        
                        lot_num = item.find_element(By.CSS_SELECTOR, '.lot').text.strip()
                        artist = item.find_element(By.CSS_SELECTOR, '.card-title').text.strip()
                        title = item.find_element(By.CSS_SELECTOR, '.card-subtitle').text.strip()
                        
                        all_results.append({
                            "회차": auction_no,
                            "페이지": page_idx,
                            "Lot": lot_num,
                            "작가": artist,
                            "작품명": title,
                            "이미지": item.find_element(By.TAG_NAME, 'img').get_attribute('src') if item.find_elements(By.TAG_NAME, 'img') else "-"
                        })
                    except:
                        continue
                
                # 만약 한 페이지당 100개씩 불러오도록 설정했으므로, 
                # 작품 수가 적으면 다음 페이지가 없는 것으로 간주하고 루프 탈출
                if len(items) < 10: # 한 페이지 아이템이 적으면 끝으로 간주
                    break
                
                page_idx += 1 # 다음 페이지로 이동

        if all_results:
            df = pd.DataFrame(all_results)
            st.success(f"✅ 총 {len(df)}건 수집 완료!")
            st.dataframe(df)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 통합 엑셀 다운로드", output.getvalue(), f"kauction_total.xlsx")

    except Exception as e:
        st.error(f"오류: {e}")
    finally:
        if 'driver' in locals(): driver.quit()