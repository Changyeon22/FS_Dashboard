"""
기존 엑셀 데이터를 웹 DB로 마이그레이션하는 스크립트
"""
import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from config import get_all_project_country_combinations, get_data_path, COUNTRY_NAMES
from web_db_handler import save_daily_metrics, save_monthly_target

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def migrate_daily_data(project: str, country: str) -> tuple:
    """
    특정 프로젝트/국가의 일일 데이터를 마이그레이션합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        tuple: (성공 레코드 수, 실패 레코드 수)
    """
    file_path = get_data_path(project, country)
    
    if not os.path.exists(file_path):
        print(f"  [WARNING] 파일이 존재하지 않습니다: {file_path}")
        return 0, 0
    
    try:
        # 엑셀 파일 읽기
        try:
            # 새 형식 (daily_data 시트)
            df = pd.read_excel(file_path, sheet_name='daily_data')
        except:
            # 구 형식 (시트 없음)
            df = pd.read_excel(file_path)
        
        if df.empty:
            print(f"  [INFO] 데이터가 없습니다.")
            return 0, 0
        
        print(f"  [INFO] {len(df)}개 레코드 발견")
        
        # 날짜 컬럼이 있는지 확인
        if 'Date' not in df.columns:
            print(f"  [ERROR] Date 컬럼이 없습니다.")
            return 0, 0
        
        # Date를 datetime으로 변환
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 컬럼 매핑 (엑셀 → DB)
        # 기존 엑셀에는 DAU, 신규 가입자, 일일 매출, MAU, 평균 세션 시간 등이 있을 수 있음
        # 새 시스템에는 DAU, DRU, DBU, SALES 등이 필요
        
        success_count = 0
        fail_count = 0
        
        # 각 행을 DB에 저장
        for idx, row in df.iterrows():
            try:
                date_str = row['Date'].strftime('%Y-%m-%d')
                
                # 지표 매핑
                metrics = {}
                
                # DAU
                if 'DAU' in row:
                    metrics['dau'] = int(row['DAU']) if pd.notna(row['DAU']) else 0
                else:
                    metrics['dau'] = 0
                
                # DRU (기존 엑셀에 없을 수 있음)
                if 'DRU' in row:
                    metrics['dru'] = int(row['DRU']) if pd.notna(row['DRU']) else 0
                else:
                    metrics['dru'] = 0
                
                # DBU (기존 엑셀에 없을 수 있음)
                if 'DBU' in row:
                    metrics['dbu'] = int(row['DBU']) if pd.notna(row['DBU']) else 0
                else:
                    metrics['dbu'] = 0
                
                # 매출
                if '일일매출' in row:
                    metrics['sales'] = float(row['일일매출']) if pd.notna(row['일일매출']) else 0.0
                elif '일일 매출' in row:
                    metrics['sales'] = float(row['일일 매출']) if pd.notna(row['일일 매출']) else 0.0
                elif 'SALES' in row:
                    metrics['sales'] = float(row['SALES']) if pd.notna(row['SALES']) else 0.0
                else:
                    metrics['sales'] = 0.0
                
                # PC방 매출
                if 'PC방매출' in row:
                    metrics['pc_room_sales'] = float(row['PC방매출']) if pd.notna(row['PC방매출']) else 0.0
                elif 'PC방 매출' in row:
                    metrics['pc_room_sales'] = float(row['PC방 매출']) if pd.notna(row['PC방 매출']) else 0.0
                else:
                    metrics['pc_room_sales'] = 0.0
                
                # PU
                if 'PU' in row:
                    metrics['pu'] = int(row['PU']) if pd.notna(row['PU']) else 0
                else:
                    metrics['pu'] = 0
                
                # 평균 동접
                if '평균동접' in row:
                    metrics['avg_concurrent'] = int(row['평균동접']) if pd.notna(row['평균동접']) else 0
                elif '평균 동접' in row:
                    metrics['avg_concurrent'] = int(row['평균 동접']) if pd.notna(row['평균 동접']) else 0
                else:
                    metrics['avg_concurrent'] = 0
                
                # 최대 동접
                if '최대동접' in row:
                    metrics['max_concurrent'] = int(row['최대동접']) if pd.notna(row['최대동접']) else 0
                elif '최대 동접' in row:
                    metrics['max_concurrent'] = int(row['최대 동접']) if pd.notna(row['최대 동접']) else 0
                else:
                    metrics['max_concurrent'] = 0
                
                # 플레이 판 수
                if '플레이판수' in row:
                    metrics['play_rounds'] = int(row['플레이판수']) if pd.notna(row['플레이판수']) else 0
                elif '플레이 판 수' in row:
                    metrics['play_rounds'] = int(row['플레이 판 수']) if pd.notna(row['플레이 판 수']) else 0
                else:
                    metrics['play_rounds'] = 0
                
                # 플레이 타임
                if '플레이타임' in row:
                    metrics['play_time_minutes'] = int(row['플레이타임']) if pd.notna(row['플레이타임']) else 0
                elif '플레이 타임' in row:
                    metrics['play_time_minutes'] = int(row['플레이 타임']) if pd.notna(row['플레이 타임']) else 0
                else:
                    metrics['play_time_minutes'] = 0
                
                # DB에 저장
                if save_daily_metrics(project, country, date_str, metrics):
                    success_count += 1
                else:
                    fail_count += 1
                    
            except Exception as e:
                print(f"  [ERROR] 레코드 {idx} 마이그레이션 실패: {e}")
                fail_count += 1
        
        return success_count, fail_count
        
    except Exception as e:
        print(f"  [ERROR] 파일 읽기 실패: {e}")
        return 0, 0


def migrate_monthly_targets(project: str, country: str) -> tuple:
    """
    특정 프로젝트/국가의 월간 목표 데이터를 마이그레이션합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        tuple: (성공 레코드 수, 실패 레코드 수)
    """
    file_path = get_data_path(project, country)
    
    if not os.path.exists(file_path):
        return 0, 0
    
    try:
        # monthly_targets 시트 읽기
        try:
            df = pd.read_excel(file_path, sheet_name='monthly_targets')
        except:
            # 시트가 없으면 스킵
            return 0, 0
        
        if df.empty:
            return 0, 0
        
        print(f"  [INFO] {len(df)}개 월간 목표 발견")
        
        # YearMonth를 datetime으로 변환
        if 'YearMonth' not in df.columns:
            return 0, 0
        
        df['YearMonth'] = pd.to_datetime(df['YearMonth'])
        
        success_count = 0
        fail_count = 0
        
        # 각 행을 DB에 저장
        for idx, row in df.iterrows():
            try:
                year_month = row['YearMonth'].strftime('%Y-%m-01')
                target_sales = float(row.get('목표매출', 0)) if pd.notna(row.get('목표매출')) else 0.0
                expected_sales = float(row.get('예상매출', 0)) if pd.notna(row.get('예상매출')) else 0.0
                
                if save_monthly_target(project, country, year_month, target_sales, expected_sales):
                    success_count += 1
                else:
                    fail_count += 1
                    
            except Exception as e:
                print(f"  [ERROR] 월간 목표 {idx} 마이그레이션 실패: {e}")
                fail_count += 1
        
        return success_count, fail_count
        
    except Exception as e:
        print(f"  [ERROR] 월간 목표 읽기 실패: {e}")
        return 0, 0


def migrate_all():
    """모든 프로젝트/국가의 데이터를 마이그레이션합니다."""
    print("=" * 80)
    print("데이터 마이그레이션 시작")
    print("=" * 80)
    
    combinations = get_all_project_country_combinations()
    print(f"\n[INFO] 대상: {len(combinations)}개 프로젝트/국가 조합\n")
    
    total_daily_success = 0
    total_daily_fail = 0
    total_target_success = 0
    total_target_fail = 0
    
    for idx, (project, country) in enumerate(combinations, 1):
        country_name = COUNTRY_NAMES.get(country, country)
        print(f"\n[{idx}/{len(combinations)}] {project} - {country_name}")
        print("-" * 60)
        
        # 일일 데이터 마이그레이션
        print("  [일일 데이터]")
        daily_success, daily_fail = migrate_daily_data(project, country)
        total_daily_success += daily_success
        total_daily_fail += daily_fail
        
        if daily_success > 0:
            print(f"    ✅ {daily_success}개 레코드 마이그레이션 완료")
        if daily_fail > 0:
            print(f"    ❌ {daily_fail}개 레코드 마이그레이션 실패")
        
        # 월간 목표 마이그레이션
        print("  [월간 목표]")
        target_success, target_fail = migrate_monthly_targets(project, country)
        total_target_success += target_success
        total_target_fail += target_fail
        
        if target_success > 0:
            print(f"    ✅ {target_success}개 레코드 마이그레이션 완료")
        if target_fail > 0:
            print(f"    ❌ {target_fail}개 레코드 마이그레이션 실패")
    
    # 최종 결과
    print("\n" + "=" * 80)
    print("데이터 마이그레이션 완료")
    print("=" * 80)
    print(f"\n[일일 데이터]")
    print(f"  ✅ 성공: {total_daily_success}개 레코드")
    print(f"  ❌ 실패: {total_daily_fail}개 레코드")
    print(f"\n[월간 목표]")
    print(f"  ✅ 성공: {total_target_success}개 레코드")
    print(f"  ❌ 실패: {total_target_fail}개 레코드")
    print("=" * 80)
    
    if total_daily_fail == 0 and total_target_fail == 0:
        print("\n✅ 모든 데이터가 성공적으로 마이그레이션되었습니다!")
    else:
        print("\n⚠️  일부 데이터 마이그레이션에 실패했습니다. 로그를 확인하세요.")


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("엑셀 데이터 → 웹 DB 마이그레이션")
    print("=" * 80)
    
    print("\n⚠️  이 작업은 기존 엑셀 파일의 데이터를 웹 DB로 이전합니다.")
    print("계속하시겠습니까? (y/n): ", end='')
    
    try:
        confirm = input().strip().lower()
        if confirm != 'y':
            print("\n[INFO] 마이그레이션이 취소되었습니다.")
            return
        
        migrate_all()
        
    except KeyboardInterrupt:
        print("\n\n[INFO] 사용자에 의해 중단되었습니다.")
        return
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류: {e}")
        return


if __name__ == "__main__":
    main()

