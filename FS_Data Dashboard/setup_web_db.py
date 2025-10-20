"""
웹 DB (로컬 SQL Server) 초기 설정 스크립트
데이터베이스와 테이블을 생성합니다.
"""
import os
import sys
import pyodbc
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 환경 변수 로드
load_dotenv()


def create_connection_string(include_db=False):
    """SQL Server 연결 문자열 생성"""
    server = os.getenv('WEB_DB_SERVER', 'localhost')
    port = os.getenv('WEB_DB_PORT', '1433')
    db_name = os.getenv('WEB_DB_NAME', 'FS_Dashboard')
    driver = os.getenv('WEB_DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    use_windows_auth = os.getenv('WEB_DB_USE_WINDOWS_AUTH', 'True').lower() == 'true'
    
    # 디버깅: 환경 변수 출력
    print(f"[DEBUG] WEB_DB_SERVER: {server}")
    print(f"[DEBUG] WEB_DB_NAME: {db_name}")
    print(f"[DEBUG] Windows Auth: {use_windows_auth}")
    
    if use_windows_auth:
        if include_db:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};Trusted_Connection=yes;"
        else:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};Trusted_Connection=yes;"
    else:
        user = os.getenv('WEB_DB_USER')
        password = os.getenv('WEB_DB_PASSWORD')
        if include_db:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={user};PWD={password};"
        else:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};UID={user};PWD={password};"
    
    print(f"[DEBUG] Connection String: {conn_str}")
    return conn_str


def create_database():
    """데이터베이스 생성"""
    db_name = os.getenv('WEB_DB_NAME', 'FS_Dashboard')
    
    try:
        print("=" * 80)
        print("[STEP 1] 데이터베이스 생성")
        print("=" * 80)
        
        # master DB에 연결
        conn_str = create_connection_string(include_db=False)
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # 데이터베이스 존재 여부 확인
        cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
        if cursor.fetchone():
            print(f"[INFO] 데이터베이스 '{db_name}'가 이미 존재합니다.")
        else:
            # 데이터베이스 생성
            cursor.execute(f"CREATE DATABASE [{db_name}]")
            print(f"[SUCCESS] 데이터베이스 '{db_name}' 생성 완료!")
        
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 데이터베이스 생성 실패: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return False


def create_tables():
    """테이블 및 인덱스 생성"""
    try:
        print("\n" + "=" * 80)
        print("[STEP 2] 테이블 생성")
        print("=" * 80)
        
        # 웹 DB에 연결
        conn_str = create_connection_string(include_db=True)
        conn = pyodbc.connect(conn_str, autocommit=False)
        cursor = conn.cursor()
        
        # 1. daily_metrics 테이블 생성
        print("\n[INFO] daily_metrics 테이블 생성 중...")
        daily_metrics_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='daily_metrics' AND xtype='U')
        BEGIN
            CREATE TABLE daily_metrics (
                id INT IDENTITY(1,1) PRIMARY KEY,
                project VARCHAR(50) NOT NULL,
                country VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                dau INT,
                dru INT,
                dbu INT,
                sales DECIMAL(15,2),
                pc_room_sales DECIMAL(15,2),
                pu INT,
                avg_concurrent INT,
                max_concurrent INT,
                play_rounds INT,
                play_time_minutes INT,
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE(),
                CONSTRAINT UQ_project_country_date UNIQUE (project, country, date)
            );
            
            CREATE INDEX idx_project_country_date ON daily_metrics(project, country, date);
            CREATE INDEX idx_date ON daily_metrics(date);
            CREATE INDEX idx_project_country ON daily_metrics(project, country);
        END
        """
        cursor.execute(daily_metrics_sql)
        print("[SUCCESS] daily_metrics 테이블 생성 완료!")
        
        # 2. monthly_targets 테이블 생성
        print("\n[INFO] monthly_targets 테이블 생성 중...")
        monthly_targets_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='monthly_targets' AND xtype='U')
        BEGIN
            CREATE TABLE monthly_targets (
                id INT IDENTITY(1,1) PRIMARY KEY,
                project VARCHAR(50) NOT NULL,
                country VARCHAR(50) NOT NULL,
                year_month DATE NOT NULL,
                target_sales DECIMAL(15,2),
                expected_sales DECIMAL(15,2),
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE(),
                CONSTRAINT UQ_target_project_country_month UNIQUE (project, country, year_month)
            );
            
            CREATE INDEX idx_target_project_country ON monthly_targets(project, country);
            CREATE INDEX idx_target_year_month ON monthly_targets(year_month);
        END
        """
        cursor.execute(monthly_targets_sql)
        print("[SUCCESS] monthly_targets 테이블 생성 완료!")
        
        # 3. collection_logs 테이블 생성 (데이터 수집 로그)
        print("\n[INFO] collection_logs 테이블 생성 중...")
        collection_logs_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='collection_logs' AND xtype='U')
        BEGIN
            CREATE TABLE collection_logs (
                id INT IDENTITY(1,1) PRIMARY KEY,
                collection_time DATETIME DEFAULT GETDATE(),
                project VARCHAR(50),
                country VARCHAR(50),
                status VARCHAR(20),
                records_inserted INT,
                records_updated INT,
                error_message TEXT,
                execution_time_seconds FLOAT
            );
            
            CREATE INDEX idx_log_time ON collection_logs(collection_time);
            CREATE INDEX idx_log_status ON collection_logs(status);
        END
        """
        cursor.execute(collection_logs_sql)
        print("[SUCCESS] collection_logs 테이블 생성 완료!")
        
        # 커밋
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("[SUCCESS] 모든 테이블이 성공적으로 생성되었습니다!")
        print("=" * 80)
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 테이블 생성 실패: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        if conn:
            conn.rollback()
        return False


def verify_setup():
    """설정 검증"""
    try:
        print("\n" + "=" * 80)
        print("[STEP 3] 설정 검증")
        print("=" * 80)
        
        conn_str = create_connection_string(include_db=True)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        print("\n[INFO] 생성된 테이블 목록:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        # 각 테이블의 레코드 수 확인
        print("\n[INFO] 테이블 레코드 수:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 레코드")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("[SUCCESS] 웹 DB 설정이 완료되었습니다!")
        print("=" * 80)
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 검증 실패: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        return False


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("웹 DB 초기 설정 스크립트")
    print("=" * 80)
    
    # 1. 데이터베이스 생성
    if not create_database():
        print("\n[ERROR] 데이터베이스 생성에 실패했습니다. 프로세스를 종료합니다.")
        return
    
    # 2. 테이블 생성
    if not create_tables():
        print("\n[ERROR] 테이블 생성에 실패했습니다. 프로세스를 종료합니다.")
        return
    
    # 3. 검증
    if not verify_setup():
        print("\n[WARNING] 검증에 실패했습니다. 설정을 확인해주세요.")
        return
    
    print("\n✅ 웹 DB 초기 설정이 모두 완료되었습니다!")
    print("\n다음 단계:")
    print("  1. 기존 엑셀 데이터 마이그레이션: python db_migration.py")
    print("  2. 데이터 수집 테스트: python data_collector.py")
    print("  3. 대시보드 실행: streamlit run dashboard.py")


if __name__ == "__main__":
    main()

