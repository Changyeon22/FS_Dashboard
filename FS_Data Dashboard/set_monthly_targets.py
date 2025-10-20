"""
월간 목표 설정 스크립트
프로젝트/국가별 월간 매출 목표 입력
"""
import sys
from datetime import datetime
from web_db_handler import save_monthly_target
from config import get_all_project_country_combinations, COUNTRY_NAMES

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


def set_target(project, country, year_month, target_sales, expected_sales):
    """월간 목표 설정"""
    country_name = COUNTRY_NAMES.get(country, country)
    print(f"[설정] {project}/{country_name} - {year_month}")
    print(f"  목표 매출: {target_sales:,}원")
    print(f"  예상 매출: {expected_sales:,}원")
    
    success = save_monthly_target(project, country, year_month, target_sales, expected_sales)
    
    if success:
        print(f"  [OK] 저장 완료\n")
    else:
        print(f"  [FAIL] 저장 실패\n")
    
    return success


def set_dummy_data():
    """더미 목표 데이터 설정 (2022년 1~2월, FS1 SEA)"""
    print("=" * 80)
    print("월간 목표 더미 데이터 입력")
    print("=" * 80)
    print("\n대상: FS1 SEA (2022년 1~2월)\n")
    
    targets = [
        # FS1 SEA - 2022년 1월
        {
            'project': 'FS1',
            'country': 'SEA',
            'year_month': '2022-01-01',
            'target_sales': 80000000,    # 8천만원
            'expected_sales': 75000000   # 7천5백만원
        },
        # FS1 SEA - 2022년 2월
        {
            'project': 'FS1',
            'country': 'SEA',
            'year_month': '2022-02-01',
            'target_sales': 85000000,    # 8천5백만원
            'expected_sales': 82000000   # 8천2백만원
        },
        # FS1 SEA - 2022년 3월
        {
            'project': 'FS1',
            'country': 'SEA',
            'year_month': '2022-03-01',
            'target_sales': 90000000,    # 9천만원
            'expected_sales': 88000000   # 8천8백만원
        }
    ]
    
    success_count = 0
    fail_count = 0
    
    for target in targets:
        if set_target(
            target['project'],
            target['country'],
            target['year_month'],
            target['target_sales'],
            target['expected_sales']
        ):
            success_count += 1
        else:
            fail_count += 1
    
    print("=" * 80)
    print(f"완료: 성공 {success_count}개, 실패 {fail_count}개")
    print("=" * 80)


def set_all_projects_dummy():
    """모든 프로젝트/국가에 기본 목표 설정"""
    print("=" * 80)
    print("전체 프로젝트/국가 기본 목표 설정")
    print("=" * 80)
    
    combinations = get_all_project_country_combinations()
    
    # 2022년 1~3월 목표
    months = ['2022-01-01', '2022-02-01', '2022-03-01']
    
    success_count = 0
    fail_count = 0
    
    for project, country in combinations:
        print(f"\n{'=' * 60}")
        print(f"{project} - {COUNTRY_NAMES.get(country, country)}")
        print('=' * 60)
        
        for month in months:
            # 프로젝트별로 다른 목표 설정
            if project == 'FS1':
                target_sales = 80000000  # 8천만원
                expected_sales = 75000000
            else:  # FS2
                target_sales = 100000000  # 1억원
                expected_sales = 95000000
            
            if set_target(project, country, month, target_sales, expected_sales):
                success_count += 1
            else:
                fail_count += 1
    
    print("\n" + "=" * 80)
    print(f"전체 완료: 성공 {success_count}개, 실패 {fail_count}개")
    print("=" * 80)


def main():
    """메인 실행"""
    print("=" * 80)
    print("월간 목표 설정 시스템")
    print("=" * 80)
    
    print("\n설정 모드 선택:")
    print("  [1] 더미 데이터 입력 (FS1 SEA, 2022년 1~3월)")
    print("  [2] 전체 프로젝트/국가 기본 목표 설정 (2022년 1~3월)")
    print("  [3] 수동 입력")
    
    try:
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == '1':
            set_dummy_data()
        
        elif choice == '2':
            confirm = input("\n전체 프로젝트/국가에 기본 목표를 설정하시겠습니까? (y/n): ").strip().lower()
            if confirm == 'y':
                set_all_projects_dummy()
            else:
                print("취소되었습니다.")
        
        elif choice == '3':
            # 수동 입력
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
            
            # 년월 입력
            year_month = input("\n년월 (YYYY-MM 형식, 예: 2022-01): ").strip()
            year_month_date = f"{year_month}-01"
            
            # 목표 매출 입력
            target_sales = float(input("목표 매출 (원): ").strip())
            expected_sales = float(input("예상 매출 (원): ").strip())
            
            # 저장
            print()
            set_target(project, country, year_month_date, target_sales, expected_sales)
        
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
    # 자동으로 더미 데이터 입력
    set_dummy_data()

