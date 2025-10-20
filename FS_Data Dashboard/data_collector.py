"""
데이터 수집 메인 로직
게임 백업 DB에서 데이터를 조회하여 웹 DB에 저장합니다.
"""
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import get_all_project_country_combinations, COUNTRY_NAMES
from backup_db_handler import fetch_daily_metrics
from web_db_handler import save_daily_metrics, log_collection

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def collect_data_for_date(project: str, country: str, date: str) -> bool:
    """
    특정 날짜의 데이터를 수집하여 저장합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        date: 날짜 (YYYY-MM-DD)
    
    Returns:
        bool: 성공 여부
    """
    try:
        start_time = time.time()
        
        # 1. 게임 백업 DB에서 데이터 조회
        print(f"  [조회] {project}/{country}/{date} 데이터 조회 중...")
        metrics = fetch_daily_metrics(project, country, date)
        
        if metrics is None:
            error_msg = f"데이터 조회 실패"
            log_collection(project, country, 'FAILURE', 0, 0, error_msg, time.time() - start_time)
            return False
        
        # 2. 웹 DB에 저장
        print(f"  [저장] 웹 DB에 저장 중...")
        success = save_daily_metrics(project, country, date, metrics)
        
        execution_time = time.time() - start_time
        
        if success:
            log_collection(project, country, 'SUCCESS', 1, 0, None, execution_time)
            print(f"  [완료] {execution_time:.2f}초 소요")
            return True
        else:
            error_msg = f"데이터 저장 실패"
            log_collection(project, country, 'FAILURE', 0, 0, error_msg, execution_time)
            return False
            
    except Exception as e:
        error_msg = str(e)
        log_collection(project, country, 'FAILURE', 0, 0, error_msg, 0)
        print(f"  [ERROR] {e}")
        return False


def get_test_date_mapping():
    """
    테스트 기간 날짜 매핑을 반환합니다.
    테스트 기간 동안 지속적으로 사용할 수 있도록 범위를 확장합니다.
    """
    # 테스트 기간 활성화 여부 확인 (환경 변수로 제어)
    test_period_active = os.getenv('TEST_PERIOD_ACTIVE', 'true').lower() == 'true'
    
    if not test_period_active:
        return {}  # 테스트 기간 비활성화 시 빈 매핑 반환
    
    # 2025년 10월 18일부터 11월 30일까지의 매핑
    mapping = {}
    
    # 2025-10-18 ~ 2025-10-31: 2022-02-16 ~ 2022-02-29
    for i in range(14):  # 10월 18일부터 31일까지 (14일)
        current_date = f"2025-10-{18 + i:02d}"
        mapped_date = f"2022-02-{16 + i:02d}"
        mapping[current_date] = mapped_date
    
    # 2025-11-01 ~ 2025-11-30: 2022-03-01 ~ 2022-03-30
    for i in range(30):  # 11월 1일부터 30일까지 (30일)
        current_date = f"2025-11-{1 + i:02d}"
        mapped_date = f"2022-03-{1 + i:02d}"
        mapping[current_date] = mapped_date
    
    return mapping


def collect_yesterday_data():
    """
    모든 프로젝트/국가의 어제 데이터를 수집합니다.
    """
    print("=" * 80)
    print("데이터 수집 시작")
    print("=" * 80)
    
    # 어제 날짜 계산
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 테스트 기간 날짜 매핑 확인
    test_mapping = get_test_date_mapping()
    actual_date = test_mapping.get(yesterday, yesterday)
    
    if actual_date != yesterday:
        print(f"\n[INFO] 테스트 기간: {yesterday} → {actual_date} 데이터 수집")
    else:
        print(f"\n[INFO] 수집 대상 날짜: {yesterday}")
    
    # 모든 프로젝트/국가 조합 가져오기
    combinations = get_all_project_country_combinations()
    print(f"[INFO] 수집 대상: {len(combinations)}개 프로젝트/국가 조합\n")
    
    success_count = 0
    fail_count = 0
    
    # 각 조합별로 데이터 수집
    for idx, (project, country) in enumerate(combinations, 1):
        country_name = COUNTRY_NAMES.get(country, country)
        print(f"\n[{idx}/{len(combinations)}] {project} - {country_name}")
        print("-" * 60)
        
        if collect_data_for_date(project, country, actual_date):
            success_count += 1
        else:
            fail_count += 1
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("데이터 수집 완료")
    print("=" * 80)
    print(f"  ✅ 성공: {success_count}개")
    print(f"  ❌ 실패: {fail_count}개")
    if actual_date != yesterday:
        print(f"  📅 테스트: {yesterday} → {actual_date}")
    else:
        print(f"  📅 날짜: {yesterday}")
    print("=" * 80)
    
    return success_count, fail_count


def collect_date_range_data(start_date: str, end_date: str):
    """
    특정 기간의 데이터를 수집합니다. (보충용)
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    """
    print("=" * 80)
    print("기간별 데이터 수집 시작")
    print("=" * 80)
    print(f"\n[INFO] 수집 기간: {start_date} ~ {end_date}")
    
    # 날짜 범위 생성
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = []
    current = start
    while current <= end:
        date_range.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # 모든 프로젝트/국가 조합 가져오기
    combinations = get_all_project_country_combinations()
    
    total_tasks = len(combinations) * len(date_range)
    print(f"[INFO] 총 {total_tasks}개 작업 (프로젝트/국가: {len(combinations)}, 날짜: {len(date_range)})\n")
    
    success_count = 0
    fail_count = 0
    task_num = 0
    
    # 각 조합 및 날짜별로 데이터 수집
    for project, country in combinations:
        country_name = COUNTRY_NAMES.get(country, country)
        print(f"\n{'=' * 60}")
        print(f"{project} - {country_name}")
        print('=' * 60)
        
        for date in date_range:
            task_num += 1
            print(f"\n[{task_num}/{total_tasks}] {date}")
            print("-" * 40)
            
            if collect_data_for_date(project, country, date):
                success_count += 1
            else:
                fail_count += 1
            
            # 서버 부하 방지를 위한 짧은 대기
            time.sleep(0.5)
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("기간별 데이터 수집 완료")
    print("=" * 80)
    print(f"  ✅ 성공: {success_count}개")
    print(f"  ❌ 실패: {fail_count}개")
    print(f"  📅 기간: {start_date} ~ {end_date}")
    print("=" * 80)
    
    return success_count, fail_count


def collect_specific_data(project: str, country: str, date: str):
    """
    특정 프로젝트/국가/날짜의 데이터를 수집합니다. (수동 실행용)
    
    Args:
        project: 프로젝트명
        country: 국가코드
        date: 날짜 (YYYY-MM-DD)
    """
    print("=" * 80)
    print("특정 데이터 수집")
    print("=" * 80)
    
    country_name = COUNTRY_NAMES.get(country, country)
    print(f"\n[INFO] 대상: {project} - {country_name}")
    print(f"[INFO] 날짜: {date}\n")
    
    success = collect_data_for_date(project, country, date)
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 데이터 수집 성공!")
    else:
        print("❌ 데이터 수집 실패!")
    print("=" * 80)
    
    return success


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("데이터 수집 시스템")
    print("=" * 80)
    
    # 실행 모드 선택
    print("\n실행 모드를 선택하세요:")
    print("  [1] 어제 데이터 수집 (기본)")
    print("  [2] 특정 기간 데이터 수집")
    print("  [3] 특정 프로젝트/국가/날짜 데이터 수집")
    
    try:
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == '1' or choice == '':
            # 어제 데이터 수집
            collect_yesterday_data()
            
        elif choice == '2':
            # 기간별 수집
            start_date = input("시작 날짜 (YYYY-MM-DD): ").strip()
            end_date = input("종료 날짜 (YYYY-MM-DD): ").strip()
            
            # 날짜 형식 검증
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                print("[ERROR] 잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력하세요.")
                return
            
            collect_date_range_data(start_date, end_date)
            
        elif choice == '3':
            # 특정 데이터 수집
            from config import PROJECTS
            
            # 프로젝트 선택
            print("\n프로젝트 선택:")
            project_list = list(PROJECTS.keys())
            for idx, proj in enumerate(project_list, 1):
                print(f"  [{idx}] {proj}")
            
            proj_idx = int(input("프로젝트 번호: ").strip()) - 1
            if proj_idx < 0 or proj_idx >= len(project_list):
                print("[ERROR] 잘못된 프로젝트 번호입니다.")
                return
            project = project_list[proj_idx]
            
            # 국가 선택
            print(f"\n{project}의 국가 선택:")
            country_list = PROJECTS[project]['countries']
            for idx, ctry in enumerate(country_list, 1):
                country_name = COUNTRY_NAMES.get(ctry, ctry)
                print(f"  [{idx}] {country_name}")
            
            ctry_idx = int(input("국가 번호: ").strip()) - 1
            if ctry_idx < 0 or ctry_idx >= len(country_list):
                print("[ERROR] 잘못된 국가 번호입니다.")
                return
            country = country_list[ctry_idx]
            
            # 날짜 입력
            date = input("\n날짜 (YYYY-MM-DD): ").strip()
            
            # 날짜 형식 검증
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                print("[ERROR] 잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력하세요.")
                return
            
            collect_specific_data(project, country, date)
            
        else:
            print("[ERROR] 잘못된 선택입니다.")
            return
            
    except KeyboardInterrupt:
        print("\n\n[INFO] 사용자에 의해 중단되었습니다.")
        return
    except ValueError as e:
        print(f"[ERROR] 입력 오류: {e}")
        return
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return


if __name__ == "__main__":
    main()

