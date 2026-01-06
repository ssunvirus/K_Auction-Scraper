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

st.set_page_config(page_title="케이옥션 통합 수집기", page_icon="🎨")
st.title("📚 케이옥션 회차별 전 정보 수집기")

st.sidebar.header("🔍 수집 범위 설정")
start_no = st.sidebar.number_input("시작 회차 번호", min_value=1, value=191)
end_no = st.sidebar.number_input("종료 회차 번호", min_value=1, value=193)

if st.button("🚀 전체 데이터 수집 시작"):
    all_results = []
    status_text = st.empty() 
    
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
            while True:
                target_url = f"https://www.k-auction.com/Auction/Major/{auction_no}?page_size=100&page={page_idx}"
                status_text.info(f"🔎 접속 중: {target_url}")
                
                driver.get(target_url)
                time.sleep(7) # 대기 시간을 7초로 조정하여 안정성 확보

                items = driver.find_elements(By.CSS_SELECTOR, 'div.col.mb-4.list-pd.major-list-pd')
                
                if not items:
                    break

                for item in items:
                    try:
                        if "card-empty" in item.get_attribute("class"): continue
                        
                        # 1. 기본 정보
                        lot_num = item.find_element(By.CSS_SELECTOR, '.lot').text.strip()
                        artist = item.find_element(By.CSS_SELECTOR, '.card-title').text.strip()
                        title = item.find_element(By.CSS_SELECTOR, '.card-subtitle').text.strip()
                        
                        # 2. 이미지 주소
                        try:
                            img_src = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
                        except:
                            img_src = "-"
                        
                        # 3. 상세 정보 (소재, 사이즈, 연도)
                        try:
                            desc_element = item.find_element(By.CSS_SELECTOR, 'p.description')
                            spans = desc_element.find_elements(By.TAG_NAME, 'span')
                            material = spans[0].text.strip() if len(spans) > 0 else "-"
                            size_year = spans[1].text.strip() if len(spans) > 1 else "-"
                            
                            size = size_year.split('|')[0].strip() if '|' in size_year else size_year
                            year = size_year.split('|')[1].strip() if '|' in size_year else "-"
                        except:
                            material, size, year = "-", "-", "-"

                        # 4. 가격 정보
                        try:
                            est_krw = item.find_element(By.CSS_SELECTOR, 'li.pull-right.text-right:not(.usd-type)').text.replace('\n', ' ').strip()
                            est_usd = item.find_element(By.CSS_SELECTOR, 'li.usd-type').text.strip()
                        except:
                            est_krw, est_usd = "-", "-"

                        all_results.append({
                            "회차": auction_no,
                            "Lot": lot_num,
                            "작가": artist,
                            "작품명": title,
                            "소재": material,
                            "사이즈": size,
                            "제작연도": year,
                            "추정가(KRW)": est_krw,
                            "추정가(USD)": est_usd,
                            "이미지주소": img_src
                        })
                    except:
                        continue
                
                if len(items) < 100: 
                    break
                page_idx += 1

        if all_results:
            status_text.success(f"✅ 총 {len(all_results)}건 수집 완료!")
            df = pd.DataFrame(all_results)
            st.dataframe(df)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button("📥 통합 상세 엑셀 다운로드", output.getvalue(), f"kauction_full_data.xlsx")
        else:
            status_text.warning("수집된 데이터가 없습니다.")

    except Exception as e:
        st.error(f"오류: {e}")
    finally:
        if 'driver' in locals(): driver.quit()