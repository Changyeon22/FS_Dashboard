"""
데이터 수집 스케줄러 서비스
Windows Task Scheduler와 함께 사용하여 정기적으로 데이터를 수집합니다.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from data_collector import collect_yesterday_data

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def main():
    """스케줄러 메인 함수"""
    
    # 로그 시작
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("=" * 80)
    print(f"데이터 수집 스케줄러 실행: {current_time}")
    print("=" * 80)
    
    try:
        # 어제 데이터 수집
        success_count, fail_count = collect_yesterday_data()
        
        # 결과 로그
        print("\n" + "=" * 80)
        print(f"스케줄러 실행 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"성공: {success_count}, 실패: {fail_count}")
        print("=" * 80)
        
        # 실패가 있으면 종료 코드 1 반환
        if fail_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\n[ERROR] 스케줄러 실행 중 오류 발생: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

