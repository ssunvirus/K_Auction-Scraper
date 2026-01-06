import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import datetime
import io

# 웹 페이지 제목 설정
st.set_page_config(page_title="서울옥션 수집기", page_icon="🏛️")
st.title("🏛️ 서울옥션 데이터 수집기")
st.write("버튼을 누르면 데이터를 수집하여 엑셀 파일로 제공합니다.")

# 버튼을 눌렀을 때만 실행
if st.button("데이터 수집 시작"):
    with st.spinner('데이터를 수집 중입니다. 잠시만 기다려 주세요 (약 10~20초)...'):
        # 1. 브라우저 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # 서버 환경에서 크롬 위치 강제 지정
        chrome_options.binary_location = "/usr/bin/chromium"
        
        # 드라이버 실행 (들여쓰기 수정 완료)
        try:
            try:
                # 방법 A: 시스템 설치된 드라이버 사용
                driver = webdriver.Chrome(options=chrome_options)
            except Exception:
                # 방법 B: 실패 시 매니저로 설치하여 사용
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

            results = []

            # 2. 서울옥션 페이지 접속
            url = "https://www.seoulauction.com/privatesale/psList"
            driver.get(url)
            time.sleep(7) # 로딩 대기

            # 3. 작품 리스트 찾기
            items = driver.find_elements(By.CSS_SELECTOR, 'div.li-inner')

            if not items:
                st.error("작품 리스트를 찾지 못했습니다.")
            else:
                for item in items:
                    try:
                        brand = item.find_element(By.CSS_SELECTOR, '.info-box .title span').text.strip()
                        product_name = item.find_element(By.CSS_SELECTOR, '.info-box .desc span').text.strip()
                        img_url = item.find_element(By.CSS_SELECTOR, '.img-align img').get_attribute('src')

                        try:
                            material = item.find_element(By.CSS_SELECTOR, '.text-over .txt-material').text.strip()
                        except:
                            material = "-"

                        try:
                            size_element = item.find_elements(By.CSS_SELECTOR, '.size_year')
                            product_size = size_element[0].text.strip() if size_element else "-"
                        except:
                            product_size = "-"

                        results.append({
                            "브랜드": brand,
                            "제품명": product_name,
                            "소재": material,
                            "사이즈": product_size,
                            "이미지주소": img_url
                        })
                    except:
                        continue
            
            # 4. 결과 출력 및 다운로드
            if results:
                df = pd.DataFrame(results)
                st.write(f"✅ 총 {len(df)}개의 데이터를 수집했습니다.")
                st.dataframe(df) # 화면에 표로 보여줌

                # 엑셀 파일 생성 (메모리상에서)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 수집된 데이터 엑셀 다운로드",
                    data=output.getvalue(),
                    file_name=f"seoul_auction_{now}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
        
        finally:
            if 'driver' in locals():
                driver.quit()