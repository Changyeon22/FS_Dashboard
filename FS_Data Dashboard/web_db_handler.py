"""
웹 DB (로컬 SQL Server) 데이터 처리 핸들러
데이터 저장, 조회, 업데이트를 담당합니다.
"""
import os
import sys
import pyodbc
import pandas as pd
from contextlib import closing
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def get_connection():
    """웹 DB 연결 생성"""
    try:
        server = os.getenv('WEB_DB_SERVER', 'localhost')
        port = os.getenv('WEB_DB_PORT', '1433')
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


def save_daily_metrics(project: str, country: str, date: str, metrics: Dict[str, Any]) -> bool:
    """
    일일 지표 데이터를 저장합니다. (INSERT or UPDATE)
    
    Args:
        project: 프로젝트명 (예: 'FS1')
        country: 국가코드 (예: 'KOR')
        date: 날짜 (YYYY-MM-DD 형식)
        metrics: 지표 데이터 딕셔너리
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
    
    Returns:
        bool: 성공 여부
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with closing(conn.cursor()) as cursor:
            # 기존 데이터 확인
            check_sql = """
                SELECT id FROM daily_metrics
                WHERE project = ? AND country = ? AND date = ?
            """
            cursor.execute(check_sql, (project, country, date))
            existing = cursor.fetchone()

            if existing:
                # UPDATE
                update_sql = """
                    UPDATE daily_metrics
                    SET dau = ?, dru = ?, dbu = ?, sales = ?, pc_room_sales = ?,
                        pu = ?, avg_concurrent = ?, max_concurrent = ?,
                        play_rounds = ?, play_time_minutes = ?,
                        updated_at = GETDATE()
                    WHERE project = ? AND country = ? AND date = ?
                """
                cursor.execute(update_sql, (
                    metrics.get('dau'),
                    metrics.get('dru'),
                    metrics.get('dbu'),
                    metrics.get('sales'),
                    metrics.get('pc_room_sales'),
                    metrics.get('pu'),
                    metrics.get('avg_concurrent'),
                    metrics.get('max_concurrent'),
                    metrics.get('play_rounds'),
                    metrics.get('play_time_minutes'),
                    project, country, date
                ))
                action = "UPDATE"
            else:
                # INSERT
                insert_sql = """
                    INSERT INTO daily_metrics
                    (project, country, date, dau, dru, dbu, sales, pc_room_sales,
                     pu, avg_concurrent, max_concurrent, play_rounds, play_time_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_sql, (
                    project, country, date,
                    metrics.get('dau'),
                    metrics.get('dru'),
                    metrics.get('dbu'),
                    metrics.get('sales'),
                    metrics.get('pc_room_sales'),
                    metrics.get('pu'),
                    metrics.get('avg_concurrent'),
                    metrics.get('max_concurrent'),
                    metrics.get('play_rounds'),
                    metrics.get('play_time_minutes')
                ))
                action = "INSERT"

        conn.commit()
        print(f"[SUCCESS] {action} - {project}/{country}/{date}")
        return True

    except pyodbc.Error as e:
        print(f"[ERROR] 데이터 저장 실패: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def query_daily_metrics(project: str, country: str, 
                       start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    일일 지표 데이터를 조회합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        start_date: 시작 날짜 (YYYY-MM-DD), None이면 전체
        end_date: 종료 날짜 (YYYY-MM-DD), None이면 전체
    
    Returns:
        pd.DataFrame: 조회된 데이터프레임 또는 None
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        # 쿼리 생성
        sql = """
            SELECT
                date as Date,
                dau as DAU,
                dru as DRU,
                dbu as DBU,
                sales as 일일매출,
                pc_room_sales as PC방매출,
                pu as PU,
                avg_concurrent as 평균동접,
                max_concurrent as 최대동접,
                play_rounds as 플레이판수,
                play_time_minutes as 플레이타임
            FROM daily_metrics
            WHERE project = ? AND country = ?
        """
        params = [project, country]

        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)

        sql += " ORDER BY date"

        # 데이터 조회
        df = pd.read_sql(sql, conn, params=params)

        # Date 컬럼을 datetime으로 변환
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        return df

    except pyodbc.Error as e:
        print(f"[ERROR] 데이터 조회 실패: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return None
    finally:
        conn.close()


def save_monthly_target(project: str, country: str, year_month: str, 
                       target_sales: float, expected_sales: float) -> bool:
    """
    월간 목표를 저장합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        year_month: 년월 (YYYY-MM-01 형식)
        target_sales: 목표 매출
        expected_sales: 예상 매출
    
    Returns:
        bool: 성공 여부
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with closing(conn.cursor()) as cursor:
            # 기존 데이터 확인
            check_sql = """
                SELECT id FROM monthly_targets
                WHERE project = ? AND country = ? AND year_month = ?
            """
            cursor.execute(check_sql, (project, country, year_month))
            existing = cursor.fetchone()

            if existing:
                # UPDATE
                update_sql = """
                    UPDATE monthly_targets
                    SET target_sales = ?, expected_sales = ?, updated_at = GETDATE()
                    WHERE project = ? AND country = ? AND year_month = ?
                """
                cursor.execute(update_sql, (
                    target_sales, expected_sales,
                    project, country, year_month
                ))
            else:
                # INSERT
                insert_sql = """
                    INSERT INTO monthly_targets
                    (project, country, year_month, target_sales, expected_sales)
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor.execute(insert_sql, (
                    project, country, year_month,
                    target_sales, expected_sales
                ))

        conn.commit()
        return True

    except pyodbc.Error as e:
        print(f"[ERROR] 월간 목표 저장 실패: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def query_monthly_targets(project: str, country: str) -> Optional[pd.DataFrame]:
    """
    월간 목표 데이터를 조회합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        pd.DataFrame: 조회된 데이터프레임 또는 None
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        sql = """
            SELECT
                year_month as YearMonth,
                target_sales as 목표매출,
                expected_sales as 예상매출
            FROM monthly_targets
            WHERE project = ? AND country = ?
            ORDER BY year_month
        """

        df = pd.read_sql(sql, conn, params=[project, country])

        # YearMonth를 datetime으로 변환
        if not df.empty and 'YearMonth' in df.columns:
            df['YearMonth'] = pd.to_datetime(df['YearMonth'])

        return df

    except pyodbc.Error as e:
        print(f"[ERROR] 월간 목표 조회 실패: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return None
    finally:
        conn.close()


def log_collection(project: str, country: str, status: str, 
                  records_inserted: int = 0, records_updated: int = 0,
                  error_message: str = None, execution_time: float = 0.0) -> bool:
    """
    데이터 수집 로그를 기록합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        status: 상태 ('SUCCESS', 'FAILURE', 'PARTIAL')
        records_inserted: 삽입된 레코드 수
        records_updated: 업데이트된 레코드 수
        error_message: 에러 메시지 (있는 경우)
        execution_time: 실행 시간 (초)
    
    Returns:
        bool: 성공 여부
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        with closing(conn.cursor()) as cursor:
            insert_sql = """
                INSERT INTO collection_logs
                (project, country, status, records_inserted, records_updated,
                 error_message, execution_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_sql, (
                project, country, status, records_inserted, records_updated,
                error_message, execution_time
            ))

        conn.commit()
        return True

    except pyodbc.Error as e:
        print(f"[WARNING] 로그 기록 실패: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"[WARNING] 로그 기록 중 오류: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_latest_date(project: str, country: str) -> Optional[str]:
    """
    특정 프로젝트/국가의 가장 최신 데이터 날짜를 반환합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        str: 최신 날짜 (YYYY-MM-DD) 또는 None
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        with closing(conn.cursor()) as cursor:
            sql = """
                SELECT MAX(date) FROM daily_metrics
                WHERE project = ? AND country = ?
            """
            cursor.execute(sql, (project, country))
            result = cursor.fetchone()

        if result and result[0]:
            return result[0].strftime('%Y-%m-%d')
        return None

    except pyodbc.Error as e:
        print(f"[ERROR] 최신 날짜 조회 실패: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return None
    finally:
        conn.close()


def test_connection() -> bool:
    """웹 DB 연결 테스트"""
    conn = get_connection()
    if not conn:
        print("[ERROR] 웹 DB 연결 실패!")
        return False

    try:
        print("[SUCCESS] 웹 DB 연결 성공!")
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    # 연결 테스트
    print("웹 DB 연결 테스트...")
    test_connection()

