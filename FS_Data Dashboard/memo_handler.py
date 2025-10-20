"""
그래프 메모 관리 핸들러
웹 DB에 메모를 저장하고 조회하는 기능을 제공합니다.
"""
import os
import pyodbc
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

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


def create_graph_memos_table():
    """그래프 메모 테이블 생성"""
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
            WHERE TABLE_NAME = 'graph_memos'
        """)
        
        if cursor.fetchone()[0] == 0:
            # 테이블이 없으면 생성
            cursor.execute("""
                CREATE TABLE graph_memos (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    project NVARCHAR(10) NOT NULL,
                    country NVARCHAR(10) NOT NULL,
                    memo_date DATE NOT NULL,
                    memo_text NVARCHAR(200) NOT NULL,
                    memo_color NVARCHAR(20) NOT NULL,
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE(),
                    UNIQUE(project, country, memo_date)
                )
            """)
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 메모 테이블 생성 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def save_memo(project: str, country: str, memo_date: str, memo_text: str, memo_color: str) -> bool:
    """
    메모를 저장합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        memo_date: 메모 날짜 (YYYY-MM-DD)
        memo_text: 메모 내용
        memo_color: 메모 색상
    
    Returns:
        bool: 성공 여부
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # 기존 메모가 있는지 확인하고 업데이트 또는 삽입
        upsert_sql = """
            MERGE graph_memos AS target
            USING (SELECT ? AS project, ? AS country, ? AS memo_date, ? AS memo_text, ? AS memo_color) AS source
            ON target.project = source.project 
               AND target.country = source.country 
               AND target.memo_date = source.memo_date
            WHEN MATCHED THEN
                UPDATE SET memo_text = source.memo_text, 
                          memo_color = source.memo_color,
                          updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (project, country, memo_date, memo_text, memo_color)
                VALUES (source.project, source.country, source.memo_date, source.memo_text, source.memo_color);
        """
        
        cursor.execute(upsert_sql, (project, country, memo_date, memo_text, memo_color))
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 메모 저장 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def delete_memo(project: str, country: str, memo_date: str) -> bool:
    """
    메모를 삭제합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
        memo_date: 메모 날짜 (YYYY-MM-DD)
    
    Returns:
        bool: 성공 여부
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        delete_sql = """
            DELETE FROM graph_memos 
            WHERE project = ? AND country = ? AND memo_date = ?
        """
        
        cursor.execute(delete_sql, (project, country, memo_date))
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"[ERROR] 메모 삭제 실패: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def get_memos(project: str, country: str) -> List[Dict[str, Any]]:
    """
    특정 프로젝트/국가의 모든 메모를 조회합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        List[Dict]: 메모 목록
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        select_sql = """
            SELECT project, country, memo_date, memo_text, memo_color, created_at, updated_at
            FROM graph_memos 
            WHERE project = ? AND country = ?
            ORDER BY memo_date DESC
        """
        
        cursor.execute(select_sql, (project, country))
        rows = cursor.fetchall()
        
        memos = []
        for row in rows:
            memos.append({
                'project': row[0],
                'country': row[1],
                'date': row[2].strftime('%Y-%m-%d'),
                'text': row[3],
                'color': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        cursor.close()
        conn.close()
        return memos
        
    except pyodbc.Error as e:
        print(f"[ERROR] 메모 조회 실패: {e}")
        if conn:
            conn.close()
        return []


def get_all_memos() -> List[Dict[str, Any]]:
    """
    모든 메모를 조회합니다.
    
    Returns:
        List[Dict]: 메모 목록
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        select_sql = """
            SELECT project, country, memo_date, memo_text, memo_color, created_at, updated_at
            FROM graph_memos 
            ORDER BY project, country, memo_date DESC
        """
        
        cursor.execute(select_sql)
        rows = cursor.fetchall()
        
        memos = []
        for row in rows:
            memos.append({
                'project': row[0],
                'country': row[1],
                'date': row[2].strftime('%Y-%m-%d'),
                'text': row[3],
                'color': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        cursor.close()
        conn.close()
        return memos
        
    except pyodbc.Error as e:
        print(f"[ERROR] 메모 조회 실패: {e}")
        if conn:
            conn.close()
        return []


if __name__ == "__main__":
    # 테이블 생성 테스트
    print("메모 테이블 생성 중...")
    if create_graph_memos_table():
        print("✅ 메모 테이블이 생성되었습니다.")
    else:
        print("❌ 메모 테이블 생성에 실패했습니다.")
