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
st.set_page_config(page_title="케이옥션 수집기", page_icon="🎨")
st.title("🎨 케이옥션 메이저 경매 수집기")
st.info("대상 주소: https://www.k-auction.com/Auction/Major/193")

# 2. 수집 버튼 클릭 시 실행
if st.button("데이터 수집 시작"):
    with st.spinner('데이터를 불러오는 중입니다... (약 1분 소요)'):
        
        # --- 크롬 옵션 설정 (반드시 드라이버 생성 전에 정의) ---
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # 서버 환경에서 크롬 위치 강제 지정 (오류 방지)
        chrome_options.binary_location = "/usr/bin/chromium"
        
        # 자동화 감지 우회 설정
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        try:
            # --- 드라이버 생성 (배포 서버 환경 최적화) ---
            # webdriver-manager가 현재 시스템의 크롬 버전을 확인하여 설치하도록 설정
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 3. 데이터 수집 로직 시작
            target_url = "https://www.k-auction.com/Auction/Major/193" 
            driver.get(target_url)
            time.sleep(15) 

            results = []
            # 작품 카드 리스트 찾기
            items = driver.find_elements(By.CSS_SELECTOR, 'div.col.mb-4.list-pd.major-list-pd')

            for item in items:
                try:
                    # 빈 카드 건너뛰기
                    if "card-empty" in item.get_attribute("class"):
                        continue
                        
                    # 4. 기본 정보 추출
                    lot_num = item.find_element(By.CSS_SELECTOR, '.lot').text.strip()
                    artist = item.find_element(By.CSS_SELECTOR, '.card-title').text.strip()
                    title = item.find_element(By.CSS_SELECTOR, '.card-subtitle').text.strip()
                    
                    # 이미지 주소 추출
                    try:
                        img_src = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
                    except:
                        img_src = "-"
                    
                    # 5. 상세 스펙 분리 (소재, 사이즈, 연도)
                    try:
                        desc_element = item.find_element(By.CSS_SELECTOR, 'p.description')
                        spans = desc_element.find_elements(By.TAG_NAME, 'span')
                        
                        material = spans[0].text.strip() if len(spans) > 0 else "-"
                        size_year_text = spans[1].text.strip() if len(spans) > 1 else "-"
                        
                        if '|' in size_year_text:
                            size = size_year_text.split('|')[0].strip()
                            year = size_year_text.split('|')[1].strip()
                        else:
                            size = size_year_text
                            year = "-"
                    except:
                        material, size, year = "-", "-", "-"

                    # 6. 가격 정보
                    try:
                        est_krw = item.find_element(By.CSS_SELECTOR, 'li.pull-right.text-right:not(.usd-type)').text.replace('\n', ' ').strip()
                        est_usd = item.find_element(By.CSS_SELECTOR, 'li.usd-type').text.strip()
                    except:
                        est_krw, est_usd = "-", "-"

                    results.append({
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

            # 7. 결과 출력 및 다운로드
            if results:
                df = pd.DataFrame(results)
                st.success(f"✅ 총 {len(df)}건의 데이터를 수집했습니다.")
                st.dataframe(df)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='KAuction_193')
                
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                file_name = f"k_auction_193_{timestamp}.xlsx"

                st.download_button(
                    label="📥 엑셀 파일 다운로드",
                    data=output.getvalue(),
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("수집된 데이터가 없습니다.")

        except Exception as e:
            st.error(f"오류 발생: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()