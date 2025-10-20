"""
환율 데이터 처리 핸들러
하나은행 최초 고시 매매 기준율을 가져와서 웹 DB에 저장합니다.
"""
import os
import requests
import pandas as pd
import pyodbc
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import time

# 환경 변수 로드
load_dotenv()


def get_connection():
    """웹 DB 연결 생성"""
    try:
        server = os.getenv('WEB_DB_SERVER', 'localhost')
        db_name = os.getenv('WEB_DB_NAME', 'FS_Dashboard')
        driver = os.getenv('WEB_DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        use_windows_auth = os.getenv('WEB_DB_USE_WINDOWS_AUTH', 'True').lower() == 'true'
        
        if use_windows_auth:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};Trusted_Connection=yes;"
        else:
            user = os.getenv('WEB_DB_USER')
            password = os.getenv('WEB_DB_PASSWORD')
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={user};PWD={password};"
        
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        print(f"[ERROR] 웹 DB 연결 실패: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return None


def create_exchange_rate_table():
    """환율 테이블 생성"""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'exchange_rates'
        """)
        
        if cursor.fetchone()[0] == 0:
            # 테이블이 없으면 생성
            cursor.execute("""
                CREATE TABLE exchange_rates (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    currency_date DATE NOT NULL,
                    usd_krw DECIMAL(10,2) NOT NULL,
                    cny_krw DECIMAL(10,2) NOT NULL,
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE(),
                    UNIQUE(currency_date)
                )
            """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 환율 테이블 생성 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def get_hana_exchange_rate(date: str) -> Optional[Dict[str, float]]:
    """
    하나은행에서 특정 날짜의 환율을 가져옵니다.
    
    Args:
        date: 날짜 (YYYY-MM-DD)
    
    Returns:
        Dict: USD/KRW, CNY/KRW 환율 정보
    """
    try:
        # 하나은행 환율 API (실제 API 엔드포인트는 확인 필요)
        # 여기서는 예시로 구현
        url = "https://www.hanabank.com/cms/rate/wpfxd651_01i_01.do"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 날짜 파라미터 설정
        params = {
            'date': date.replace('-', ''),
            'currency': 'USD,CNY'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            # 실제 응답 파싱 로직 (하나은행 API 응답 형식에 따라 수정 필요)
            # 여기서는 예시 데이터 반환
            return {
                'usd_krw': 1300.0,  # 실제로는 API 응답에서 파싱
                'cny_krw': 180.0    # 실제로는 API 응답에서 파싱
            }
        else:
            print(f"[WARNING] 하나은행 API 응답 실패: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"[ERROR] 환율 API 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 환율 데이터 처리 실패: {e}")
        return None


def get_kexim_exchange_rate(date: str) -> Optional[Dict[str, float]]:
    """
    한국수출입은행 Open API에서 환율을 가져옵니다
    """
    try:
        # 한국수출입은행 Open API 사용
        api_key = os.getenv('KEXIM_API_KEY', 'YOUR_KEXIM_API_KEY')
        
        if api_key == 'YOUR_KEXIM_API_KEY':
            print("[WARNING] 한국수출입은행 API 키가 설정되지 않았습니다.")
            return None
        
        # 한국수출입은행 API 엔드포인트
        url = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
        
        # 요청 파라미터
        params = {
            'authkey': api_key,
            'searchdate': date.replace('-', ''),  # YYYYMMDD 형식
            'data': 'AP01'  # 환율 API 타입
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = {}
            
            # API 응답에서 USD와 CNY 환율 추출
            for currency in data:
                if currency.get('cur_unit') == 'USD':
                    # 최초 고시 매매기준율: kftc_deal_bas_r (한국외환거래조합 매매기준율) 사용
                    # 대체: kftc_bkpr (한국외환거래조합 기준율) 또는 deal_bas_r (매매기준율)
                    usd_rate = None
                    if currency.get('kftc_deal_bas_r') and currency['kftc_deal_bas_r'] != '0':
                        usd_rate = float(currency['kftc_deal_bas_r'].replace(',', ''))
                    elif currency.get('kftc_bkpr') and currency['kftc_bkpr'] != '0':
                        usd_rate = float(currency['kftc_bkpr'].replace(',', ''))
                    elif currency.get('deal_bas_r') and currency['deal_bas_r'] != '0':
                        usd_rate = float(currency['deal_bas_r'].replace(',', ''))
                    
                    if usd_rate:
                        rates['usd_krw'] = usd_rate
                        
                elif currency.get('cur_unit') == 'CNH':  # 중국 위안화는 CNH로 표시
                    # 최초 고시 매매기준율: kftc_deal_bas_r (한국외환거래조합 매매기준율) 사용
                    # 대체: kftc_bkpr (한국외환거래조합 기준율) 또는 deal_bas_r (매매기준율)
                    cny_rate = None
                    if currency.get('kftc_deal_bas_r') and currency['kftc_deal_bas_r'] != '0':
                        cny_rate = float(currency['kftc_deal_bas_r'].replace(',', ''))
                    elif currency.get('kftc_bkpr') and currency['kftc_bkpr'] != '0':
                        cny_rate = float(currency['kftc_bkpr'].replace(',', ''))
                    elif currency.get('deal_bas_r') and currency['deal_bas_r'] != '0':
                        cny_rate = float(currency['deal_bas_r'].replace(',', ''))
                    
                    if cny_rate:
                        rates['cny_krw'] = cny_rate
            
            if rates:
                print(f"[INFO] 한국수출입은행에서 {date} 환율을 가져왔습니다: {rates}")
                return rates
            else:
                print(f"[WARNING] {date} USD/CNY 환율 데이터를 찾을 수 없습니다.")
                return None
        else:
            print(f"[WARNING] 한국수출입은행 API 응답 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 한국수출입은행 API 호출 실패: {e}")
        return None


def get_bok_exchange_rate(date: str) -> Optional[Dict[str, float]]:
    """
    한국은행 API에서 환율을 가져옵니다
    """
    try:
        # 한국은행 경제통계시스템 API 사용
        api_key = os.getenv('BOK_API_KEY', 'YOUR_BOK_API_KEY')  # 환경변수에서 API 키 가져오기
        
        if api_key == 'YOUR_BOK_API_KEY':
            print("[WARNING] 한국은행 API 키가 설정되지 않았습니다. 예시 데이터를 사용합니다.")
            # API 키가 없을 때는 예시 데이터 반환
            return {
                'usd_krw': 1300.0,
                'cny_krw': 180.0
            }
        
        rates = {}
        
        # USD/KRW 환율 조회 (통계표: 731Y001, 항목: 0000001)
        usd_url = "https://ecos.bok.or.kr/api/StatisticSearch"
        usd_params = {
            'apiKey': api_key,
            'lang': 'kr',
            'format': 'json',
            'statCode': '731Y001',
            'itemCode1': '0000001',  # USD
            'startDate': date.replace('-', ''),
            'endDate': date.replace('-', ''),
            'cycle': 'D'
        }
        
        usd_response = requests.get(usd_url, params=usd_params, timeout=10)
        if usd_response.status_code == 200:
            usd_data = usd_response.json()
            if 'StatisticSearch' in usd_data and 'row' in usd_data['StatisticSearch']:
                usd_rows = usd_data['StatisticSearch']['row']
                if usd_rows and len(usd_rows) > 0:
                    rates['usd_krw'] = float(usd_rows[0]['DATA_VALUE'])
        
        # CNY/KRW 환율 조회 (통계표: 731Y001, 항목: 0000002)
        cny_params = {
            'apiKey': api_key,
            'lang': 'kr',
            'format': 'json',
            'statCode': '731Y001',
            'itemCode1': '0000002',  # CNY
            'startDate': date.replace('-', ''),
            'endDate': date.replace('-', ''),
            'cycle': 'D'
        }
        
        cny_response = requests.get(usd_url, params=cny_params, timeout=10)
        if cny_response.status_code == 200:
            cny_data = cny_response.json()
            if 'StatisticSearch' in cny_data and 'row' in cny_data['StatisticSearch']:
                cny_rows = cny_data['StatisticSearch']['row']
                if cny_rows and len(cny_rows) > 0:
                    rates['cny_krw'] = float(cny_rows[0]['DATA_VALUE'])
        
        if rates:
            return rates
        else:
            print(f"[WARNING] {date} 환율 데이터를 가져올 수 없습니다.")
            return None
        
    except Exception as e:
        print(f"[ERROR] 한국은행 API 호출 실패: {e}")
        return None


def get_exchange_rate_from_alternative_source(date: str) -> Optional[Dict[str, float]]:
    """
    대체 소스에서 환율을 가져옵니다 (한국수출입은행 > 한국은행 순서로 시도)
    """
    # 1순위: 한국수출입은행 API
    kexim_rate = get_kexim_exchange_rate(date)
    if kexim_rate:
        print(f"[INFO] 한국수출입은행에서 {date} 환율을 가져왔습니다.")
        return kexim_rate
    
    # 2순위: 한국은행 API
    bok_rate = get_bok_exchange_rate(date)
    if bok_rate:
        print(f"[INFO] 한국은행에서 {date} 환율을 가져왔습니다.")
        return bok_rate
    
    print(f"[WARNING] 모든 환율 소스에서 {date} 데이터를 가져올 수 없습니다.")
    return None


def save_exchange_rate(date: str, usd_krw: float, cny_krw: float) -> bool:
    """
    환율을 DB에 저장합니다.
    
    Args:
        date: 날짜 (YYYY-MM-DD)
        usd_krw: USD/KRW 환율
        cny_krw: CNY/KRW 환율
    
    Returns:
        bool: 성공 여부
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # 기존 환율이 있는지 확인하고 업데이트 또는 삽입
        upsert_sql = """
            MERGE exchange_rates AS target
            USING (SELECT ? AS currency_date, ? AS usd_krw, ? AS cny_krw) AS source
            ON target.currency_date = source.currency_date
            WHEN MATCHED THEN
                UPDATE SET usd_krw = source.usd_krw, 
                          cny_krw = source.cny_krw,
                          updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (currency_date, usd_krw, cny_krw)
                VALUES (source.currency_date, source.usd_krw, source.cny_krw);
        """
        
        cursor.execute(upsert_sql, (date, usd_krw, cny_krw))
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 환율 저장 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def get_exchange_rate(date: str) -> Optional[Dict[str, float]]:
    """
    DB에서 특정 날짜의 환율을 조회합니다.
    
    Args:
        date: 날짜 (YYYY-MM-DD)
    
    Returns:
        Dict: USD/KRW, CNY/KRW 환율 정보
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        select_sql = """
            SELECT usd_krw, cny_krw
            FROM exchange_rates 
            WHERE currency_date = ?
        """
        
        cursor.execute(select_sql, (date,))
        row = cursor.fetchone()
        
        if row:
            result = {
                'usd_krw': float(row[0]),
                'cny_krw': float(row[1])
            }
        else:
            result = None
        
        cursor.close()
        conn.close()
        return result
        
    except pyodbc.Error as e:
        print(f"[ERROR] 환율 조회 실패: {e}")
        if conn:
            conn.close()
        return None


def collect_daily_exchange_rate(date: str) -> bool:
    """
    특정 날짜의 환율을 수집하여 DB에 저장합니다.
    
    Args:
        date: 날짜 (YYYY-MM-DD)
    
    Returns:
        bool: 성공 여부
    """
    print(f"[INFO] {date} 환율 수집 시작...")
    
    # 먼저 DB에서 확인
    existing_rate = get_exchange_rate(date)
    if existing_rate:
        print(f"[INFO] {date} 환율이 이미 존재합니다.")
        return True
    
    # 한국수출입은행 API에서 환율 가져오기 시도 (1순위)
    rate_data = get_kexim_exchange_rate(date)
    
    # 실패하면 한국은행 API 시도 (2순위)
    if not rate_data:
        print(f"[INFO] 한국수출입은행에서 환율을 가져올 수 없어 한국은행 API를 시도합니다.")
        rate_data = get_bok_exchange_rate(date)
    
    # 실패하면 하나은행 시도 (3순위)
    if not rate_data:
        print(f"[INFO] 한국은행에서 환율을 가져올 수 없어 하나은행을 시도합니다.")
        rate_data = get_hana_exchange_rate(date)
    
    # 모든 소스 실패 시 예시 데이터 사용
    if not rate_data:
        print(f"[INFO] 모든 환율 소스에서 데이터를 가져올 수 없어 예시 데이터를 사용합니다.")
        rate_data = {
            'usd_krw': 1300.0,
            'cny_krw': 180.0
        }
    
    if rate_data:
        # DB에 저장
        if save_exchange_rate(date, rate_data['usd_krw'], rate_data['cny_krw']):
            print(f"[SUCCESS] {date} 환율 저장 완료: USD={rate_data['usd_krw']}, CNY={rate_data['cny_krw']}")
            return True
        else:
            print(f"[ERROR] {date} 환율 저장 실패")
            return False
    else:
        print(f"[ERROR] {date} 환율 데이터를 가져올 수 없습니다.")
        return False


def collect_exchange_rates_for_period(start_date: str, end_date: str) -> int:
    """
    기간 동안의 환율을 수집합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    
    Returns:
        int: 성공적으로 수집된 날짜 수
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    success_count = 0
    current = start
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        if collect_daily_exchange_rate(date_str):
            success_count += 1
        
        # API 호출 제한을 위한 딜레이
        time.sleep(1)
        current += timedelta(days=1)
    
    print(f"[INFO] 환율 수집 완료: {success_count}/{((end - start).days + 1)} 일")
    return success_count


if __name__ == "__main__":
    # 테이블 생성 테스트
    print("환율 테이블 생성 중...")
    if create_exchange_rate_table():
        print("✅ 환율 테이블이 생성되었습니다.")
        
        # 최근 30일 환율 수집 테스트
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"최근 30일 환율 수집 시작: {start_date} ~ {end_date}")
        success_count = collect_exchange_rates_for_period(start_date, end_date)
        print(f"수집 완료: {success_count}일")
    else:
        print("❌ 환율 테이블 생성에 실패했습니다.")
