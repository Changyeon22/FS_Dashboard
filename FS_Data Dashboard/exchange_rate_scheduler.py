"""
환율 수집 스케줄러 서비스
평일 오전 9시에 환율 데이터를 수집합니다.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from exchange_rate_handler import collect_daily_exchange_rate

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def is_weekday():
    """오늘이 평일인지 확인합니다."""
    today = datetime.now().weekday()  # 0=월요일, 6=일요일
    return today < 5  # 월요일(0)~금요일(4)


def is_weekday_test():
    """테스트용: 주말 시뮬레이션"""
    return False  # 테스트용으로 주말로 설정


def collect_today_exchange_rate():
    """오늘 환율을 수집합니다."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 80)
    print(f"환율 수집 스케줄러 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 평일 확인
    if not is_weekday():
        print(f"[INFO] 오늘은 주말입니다. 환율 수집을 건너뜁니다.")
        print("=" * 80)
        return True
    
    print(f"[INFO] 평일 확인: 환율 수집을 시작합니다.")
    print(f"[INFO] 수집 대상 날짜: {today}")
    
    try:
        # 오늘 환율 수집
        success = collect_daily_exchange_rate(today)
        
        if success:
            print(f"[SUCCESS] {today} 환율 수집 완료")
            return True
        else:
            print(f"[ERROR] {today} 환율 수집 실패")
            return False
            
    except Exception as e:
        print(f"[ERROR] 환율 수집 중 오류 발생: {e}")
        return False


def main():
    """환율 수집 스케줄러 메인 함수"""
    
    # 로그 시작
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("=" * 80)
    print(f"환율 수집 스케줄러 실행: {current_time}")
    print("=" * 80)
    
    try:
        # 오늘 환율 수집
        success = collect_today_exchange_rate()
        
        # 결과 로그
        print("\n" + "=" * 80)
        print(f"환율 수집 스케줄러 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"결과: {'성공' if success else '실패'}")
        print("=" * 80)
        
        # 실패 시 종료 코드 1 반환
        if not success:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\n[ERROR] 환율 수집 스케줄러 실행 중 오류 발생: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
