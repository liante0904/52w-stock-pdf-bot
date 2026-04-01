import requests
import pandas as pd
import numpy as np
import asyncio
import sys
from tqdm import tqdm
import os
from dotenv import load_dotenv
from datetime import datetime

now = datetime.now()

print("현재 : ", now)
print("현재 날짜 : ", now.date())
print("현재 시간 : ", now.time())
print("timestamp : ", now.timestamp())
print("년 : ", now.year)
print("월 : ", now.month)
print("일 : ", now.day)
print("시 : ", now.hour)
print("분 : ", now.minute)
print("초 : ", now.second)
print("마이크로초 : ", now.microsecond)
print("요일 : ", now.weekday())
print("문자열 변환 : ", now.strftime('%Y%m%d')[2:8])

# 현재 파일 기준으로 상위 디렉토리에 있는 .env 파일 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path=env_path)

pdf_save_dir = os.getenv('PDF_SAVE_DIR', '.')
if not os.path.exists(pdf_save_dir):
    os.makedirs(pdf_save_dir, exist_ok=True)

pdf_file_name = os.path.join(pdf_save_dir, f"{now.strftime('%Y%m%d')[2:8]}_snp500_52wk_high.pdf")

# 현재 스크립트의 상위 디렉터리 경로를 추가
sys.path.append(base_dir)

from utils.pdf_util import create_pdf

# 현재 파일 기준으로 상위 디렉토리에 있는 .env 파일 경로 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path=env_path)

# 환경 변수 사용
env = os.getenv('ENV')
naver_api_snp = os.getenv('NAVER_API_SNP500')


# 네이버 API에서 S&P 500 종목 가져오기
def get_sp500_symbols_from_naver():
    url = naver_api_snp
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        data = response.json()
        stocks = data.get("stocks", [])
        print(f"총 {len(stocks)}개의 S&P 500 종목을 가져왔습니다.")
        symbols_with_names = [(stock["reutersCode"], stock["stockName"]) for stock in stocks]
        print(f"총 {len(symbols_with_names)}개의 S&P 500 종목을 가져왔습니다.")
        print(f"symbols_with_names: {symbols_with_names}")
        return symbols_with_names
    except requests.RequestException as e:
        print(f"데이터를 가져오는 중 에러가 발생했습니다: {e}")
        return []

# 52주 신고가 종목 확인 (네이버 API 사용)
async def find_52_week_high(stock_code):
    try:
        url = f"https://api.stock.naver.com/stock/{stock_code}/basic"
        
        # 네이버 API 호출
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        
        # JSON 데이터 파싱
        data = response.json()
        stock_info = data.get('stockItemTotalInfos', [])
        
        # 52주 최고가와 현재 가격 추출
        high_52_week = None
        close_price = float(data.get('closePrice', 0).replace(',', ''))
        
        for item in stock_info:
            if item['code'] == 'highPriceOf52Weeks':
                high_52_week = float(item['value'].replace(',', ''))  # 쉼표 제거 후 float 변환
            if item['code'] == 'industryGroupKor':
                sector = item['value']

        # 현재 가격이 52주 최고가와 거의 동일한지 확인
        is_high = np.isclose(close_price, high_52_week, rtol=0.01)  # 1% 이내 오차 허용
        print(f"{stock_code}: 현재가 {close_price}, 52주 최고가 {high_52_week} -> {'신고가' if is_high else '신고가 아님'}")
        return is_high, sector
    
    except requests.RequestException as e:
        print(f"네이버 API 호출 중 에러 발생 ({stock_code}): {e}")
        return False
    except Exception as e:
        print(f"데이터 처리 중 에러 발생 ({stock_code}): {e}")
        return False
    
# 회사의 사업내용 및 업종 가져오기
async def get_company_profile(stock_code):
    try:
        url = f"https://api.stock.naver.com/stock/{stock_code}/integration"
        
        # 네이버 API 호출
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        
        # JSON 데이터 파싱
        stock_info = response.json()
        print(f"Raw stock_info: {stock_info}")  # 디버깅용 출력
        
        # 사업 내용 추출
        if 'corporateOverview' in stock_info:
            description = stock_info['corporateOverview']
            print(description)
        else:
            print(f"'corporateOverview' 키가 stock_info에 없습니다.")
            return False
        
        return description
        
    except requests.RequestException as e:
        print(f"네이버 API 호출 중 에러 발생 ({stock_code}): {e}")
        return False
    except Exception as e:
        print(f"데이터 처리 중 에러 발생 ({stock_code}): {e}")
        return False

# 메인 함수: S&P 500 종목 분석
async def analyze_sp500():
    print("S&P 500 종목 목록을 네이버 API에서 가져오는 중...")
    sp500_tickers_with_names = get_sp500_symbols_from_naver()
    if not sp500_tickers_with_names:
        print("S&P 500 목록을 가져오지 못했습니다.")
        return None, None  # 결과가 없으면 None 반환

    # 52주 신고가 종목을 저장할 리스트
    high_52_week_stocks = []
    send_pdf_file_name = None  # PDF 파일명을 기본값으로 초기화
    print("52주 신고가 종목을 분석 중...")

    # tqdm 진행 상태와 종목별 처리 메시지를 함께 출력
    with tqdm(total=len(sp500_tickers_with_names), desc="Analyzing", unit="stock") as pbar:
        for idx, (ticker, name) in enumerate(sp500_tickers_with_names):
            profile = {}
            is_high, profile['sector'] = await find_52_week_high(ticker)
            pbar.update(1)  # 진행 상황 업데이트
            print(f"Analyzing {ticker} ({idx + 1} of {len(sp500_tickers_with_names)})...")
            if not is_high:
                print(f"{name} ({ticker}): 52주 신고가 아님.")
                continue  # 52주 신고가가 아니면 건너뜀
            profile['description'] = await get_company_profile(ticker)
            high_52_week_stocks.append((ticker, name, profile['sector'], profile['description']))
            # profile['sector'] 기준으로 정렬
            high_52_week_stocks.sort(key=lambda x: x[1])  # sector(두 번째 요소) 기준으로 정렬
            print(f"{ticker}: 52주 신고가 종목으로 추가됨.")

    print('=' * 40)
    print("S&P 500 52주 신고가 종목 리스트")
    print('=' * 40)
    
    high_52_week_stocks_list = "S&P 500 52주 신고가 종목 리스트\n\n"
    
    if not high_52_week_stocks:
        high_52_week_stocks_list += "\n52주 신고가 종목이 없습니다."
        print(f"{high_52_week_stocks_list}")
    else:
        # 고정폭 글꼴을 사용한 표 형식
        header = f"{'티커':<10}{'종목명':<20}{'업종':<20}"
        separator = "-" * len(header)
        high_52_week_stocks_list += "```\n"  # 시작 부분에 줄바꿈 추가
        high_52_week_stocks_list += header + "\n"  # 헤더 뒤에 줄바꿈 추가
        high_52_week_stocks_list += separator + "\n"  # 구분선 뒤에 줄바꿈 추가

        for ticker, name, sector, description in high_52_week_stocks:
            high_52_week_stocks_list += f"{ticker:<10}{name:<20}{sector:<20}\n"

        high_52_week_stocks_list += "```"

        
    if not high_52_week_stocks:
        print("\n52주 신고가 종목이 없습니다.")
    else:
        # 결과를 데이터프레임으로 정리
        high_52_week_df = pd.DataFrame(high_52_week_stocks, columns=['Ticker', 'Name', 'Sector', 'Business Profile'])

        # 업종별로 그룹화하여 출력
        grouped_by_sector = high_52_week_df.groupby('Sector')
        for sector, group in grouped_by_sector:
            print(f"\n업종: {sector}")
            for idx, row in group.iterrows():
                print(f"티커: {row['Ticker']}\n종목명: {row['Name']}\n사업내용: {row['Business Profile']}")

        print("\nS&P 500 52주 신고가 종목 (업종별 분류 및 한글 번역된 사업내용 포함):")
        # PDF 생성
        send_pdf_file_name = ''
        if grouped_by_sector:
            send_pdf_file_name = create_pdf(pdf_file_name, grouped_by_sector)
            print(f"\nPDF 파일이 생성되었습니다: {send_pdf_file_name}")
        else:
            print(f"52주 신고가 데이터가 없거나 올바르지 않습니다. => {grouped_by_sector}")
        return high_52_week_stocks_list, send_pdf_file_name

if __name__ == '__main__':
    # 메인 함수 실행
    asyncio.run(analyze_sp500())
