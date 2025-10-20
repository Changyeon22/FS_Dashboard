"""
게임 백업 DB (SQL Server) 데이터 조회 핸들러
프로젝트/국가별 DB에서 지표 데이터를 조회합니다.

⚠️ 주의: 실제 DB 구조에 맞춰 쿼리를 수정해야 합니다.
"""
import os
import sys
import pyodbc
from contextlib import closing
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from config import PROJECTS, get_country_specific_config

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def get_backup_db_connection(project: str, country: str):
    """
    게임 백업 DB 연결 생성
    
    Args:
        project: 프로젝트명 (예: 'FS1')
        country: 국가코드 (예: 'KOR')
    
    Returns:
        pyodbc.Connection: DB 연결 객체 또는 None
    """
    try:
        server = os.getenv('BACKUP_DB_SERVER', '10.20.252.178')
        port = os.getenv('BACKUP_DB_PORT', '1433')
        driver = os.getenv('BACKUP_DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        
        # 국가별 설정 가져오기
        country_config = get_country_specific_config(project, country)
        db_name = country_config['db_name']
        
        print(f"[INFO] {project}/{country} DB: {db_name}")
        
        # 인증 방식 확인
        user = os.getenv('BACKUP_DB_USER')
        password = os.getenv('BACKUP_DB_PASSWORD')
        
        if user and password:
            conn_str = f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={db_name};UID={user};PWD={password};"
        else:
            conn_str = f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={db_name};Trusted_Connection=yes;"
        
        conn = pyodbc.connect(conn_str, timeout=30)
        return conn
        
    except pyodbc.Error as e:
        print(f"[ERROR] 게임 백업 DB 연결 실패 ({project}/{country}): {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류 ({project}/{country}): {e}")
        return None


def fetch_daily_metrics(project: str, country: str, date: str) -> Optional[Dict[str, Any]]:
    """
    특정 날짜의 일일 지표 데이터를 조회합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        date: 조회할 날짜 (YYYY-MM-DD 형식)
    
    Returns:
        dict: 지표 데이터 딕셔너리 또는 None
              {
                  'dau': 1000,
                  'dru': 50,
                  'dbu': 100,
                  'sales': 500000.00,
                  'pc_room_sales': 100000.00,
                  'pu': 80,
                  'avg_concurrent': 150,
                  'max_concurrent': 300,
                  'play_rounds': 5000,
                  'play_time_minutes': 120000
              }
    """
    conn = get_backup_db_connection(project, country)
    if not conn:
        return None

    try:
        with closing(conn.cursor()) as cursor:
            # BIWORK.DailyStatistics_New 테이블에서 데이터 조회
            # ⚠️ 주의: 프로젝트/국가를 구분하는 컬럼이 있다면 WHERE 조건에 추가해야 합니다.
            sql = """
                SELECT
                    -- DAU (Daily Active Users) - 일일 접속 유저
                    ISNULL(DAU, 0) as dau,

                    -- DRU (Daily Register Users) - 일일 신규 유저
                    ISNULL(DRU, 0) as dru,

                    -- DBU (Daily Back Users) - 일일 복귀 유저
                    ISNULL(DBU, 0) as dbu,

                    -- SALES - 매출
                    ISNULL(SALES, 0) as sales,

                    -- PC방 매출 (테이블에 없음)
                    0 as pc_room_sales,

                    -- PU (Purchase Users) - 구매 유저 수
                    ISNULL(PU, 0) as pu,

                    -- ACU (Average Current Users) - 평균 동시 접속 유저
                    ISNULL(ACU, 0) as avg_concurrent,

                    -- MCU (Maximum Current Users) - 최대 동시 접속 유저
                    ISNULL(MCU, 0) as max_concurrent,

                    -- A_PLAY_CNT - 평균 게임 플레이 판수
                    ISNULL(A_PLAY_CNT, 0) as play_rounds,

                    -- A_PLAY_TIME - 평균 게임 플레이 타임 (분 단위로 가정)
                    ISNULL(A_PLAY_TIME, 0) as play_time_minutes

                FROM DailyStatistics_New
                WHERE StatDate = ?

                -- ⚠️ 프로젝트/국가 구분 컬럼이 있다면 아래 주석을 해제하고 실제 컬럼명으로 수정하세요
                -- AND [프로젝트컬럼] = ?
                -- AND [국가컬럼] = ?
            """

            cursor.execute(sql, (date,))
            row = cursor.fetchone()

        if not row:
            print(f"[WARNING] {project}/{country}/{date} 데이터를 찾을 수 없습니다.")
            return None

        # 결과를 딕셔너리로 변환
        metrics = {
            'dau': int(row.dau) if row.dau is not None else 0,
            'dru': int(row.dru) if row.dru is not None else 0,
            'dbu': int(row.dbu) if row.dbu is not None else 0,
            'sales': float(row.sales) if row.sales is not None else 0.0,
            'pc_room_sales': float(row.pc_room_sales) if row.pc_room_sales is not None else 0.0,
            'pu': int(row.pu) if row.pu is not None else 0,
            'avg_concurrent': int(row.avg_concurrent) if row.avg_concurrent is not None else 0,
            'max_concurrent': int(row.max_concurrent) if row.max_concurrent is not None else 0,
            'play_rounds': int(row.play_rounds) if row.play_rounds is not None else 0,
            'play_time_minutes': int(row.play_time_minutes) if row.play_time_minutes is not None else 0,
        }

        print(f"[SUCCESS] {project}/{country}/{date} 데이터 조회 완료")
        return metrics

    except pyodbc.Error as e:
        print(f"[ERROR] 데이터 조회 실패 ({project}/{country}/{date}): {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류 ({project}/{country}/{date}): {e}")
        return None
    finally:
        conn.close()


def test_connection(project: str, country: str) -> bool:
    """
    특정 프로젝트/국가의 게임 백업 DB 연결 테스트
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        bool: 연결 성공 여부
    """
    conn = get_backup_db_connection(project, country)
    if not conn:
        print(f"[ERROR] {project}/{country} 게임 백업 DB 연결 실패!")
        return False

    try:
        print(f"[SUCCESS] {project}/{country} 게임 백업 DB 연결 성공!")

        # 테이블 목록 조회 (선택)
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute("""
                    SELECT TOP 5 TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """)
                tables = cursor.fetchall()
                print(f"[INFO] 사용 가능한 테이블 (처음 5개):")
                for table in tables:
                    print(f"  - {table[0]}")
        except pyodbc.Error:
            pass

        return True
    finally:
        conn.close()


def test_all_connections():
    """모든 프로젝트/국가 조합의 연결 테스트"""
    print("=" * 80)
    print("모든 게임 백업 DB 연결 테스트")
    print("=" * 80)
    
    from config import get_all_project_country_combinations
    
    combinations = get_all_project_country_combinations()
    success_count = 0
    fail_count = 0
    
    for project, country in combinations:
        print(f"\n[TEST] {project}/{country}")
        if test_connection(project, country):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 80)
    print(f"[결과] 성공: {success_count}, 실패: {fail_count}")
    print("=" * 80)
    
    if fail_count > 0:
        print("\n[TIP] .env 파일의 DB 연결 정보를 확인해주세요.")
        print("[TIP] 각 프로젝트/국가별 DB 이름이 올바르게 설정되어 있는지 확인하세요.")


if __name__ == "__main__":
    # 모든 연결 테스트
    test_all_connections()
    
    print("\n" + "=" * 80)
    print("⚠️ 중요: backup_db_handler.py의 SQL 쿼리를 실제 DB 구조에 맞게 수정해야 합니다!")
    print("=" * 80)
    print("\n다음 정보를 확인하고 fetch_daily_metrics() 함수의 SQL을 수정하세요:")
    print("  1. 테이블명")
    print("  2. 날짜 컬럼명")
    print("  3. 각 지표별 컬럼명 또는 계산 로직")
    print("     - DAU, DRU, DBU, SALES, PC방 매출, PU, 평균 동접, 최대 동접, 플레이 판 수, 플레이 타임")

