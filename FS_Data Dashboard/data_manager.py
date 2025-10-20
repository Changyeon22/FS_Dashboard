"""
데이터 로드 및 관리 모듈 (월간 목표 포함)
웹 DB 기반으로 데이터를 로드합니다.
"""
import os
import pandas as pd
from datetime import datetime
import openpyxl
from config import get_data_path
from web_db_handler import query_daily_metrics, query_monthly_targets


def load_daily_data(project: str, country: str, start_date: str = None, end_date: str = None) -> pd.DataFrame | None:
    """
    일일 지표 데이터를 로드합니다. (웹 DB에서)
    
    Args:
        project: 프로젝트명
        country: 국가코드
        start_date: 시작 날짜 (YYYY-MM-DD), 선택사항
        end_date: 종료 날짜 (YYYY-MM-DD), 선택사항
    
    Returns:
        pd.DataFrame: 일일 지표 데이터 또는 None
    """
    try:
        # 웹 DB에서 데이터 조회
        df = query_daily_metrics(project, country, start_date, end_date)
        
        if df is not None and not df.empty:
            # Date 컬럼이 있으면 정렬
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')
            return df
        
        return None
        
    except Exception as e:
        print(f"[ERROR] 데이터 로드 실패 ({project}/{country}): {e}")
        return None


def load_monthly_targets(project: str, country: str) -> pd.DataFrame | None:
    """
    월간 목표 데이터를 로드합니다. (웹 DB에서)
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        pd.DataFrame: 월간 목표 데이터 또는 None
    """
    try:
        # 웹 DB에서 데이터 조회
        df = query_monthly_targets(project, country)
        
        if df is not None and not df.empty:
            if 'YearMonth' in df.columns:
                df['YearMonth'] = pd.to_datetime(df['YearMonth'])
            return df
        
        return None
        
    except Exception as e:
        print(f"[ERROR] 월간 목표 로드 실패 ({project}/{country}): {e}")
        return None


def save_data_with_targets(project: str, country: str, daily_df: pd.DataFrame, targets_df: pd.DataFrame = None):
    """일일 데이터와 월간 목표를 함께 저장합니다."""
    file_path = get_data_path(project, country)
    
    # 디렉토리 생성
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # 일일 데이터 저장
        daily_df.to_excel(writer, sheet_name='daily_data', index=False)
        
        # 월간 목표 저장
        if targets_df is not None and not targets_df.empty:
            targets_df.to_excel(writer, sheet_name='monthly_targets', index=False)
        else:
            # 기본 월간 목표 생성
            default_targets = create_default_monthly_targets()
            default_targets.to_excel(writer, sheet_name='monthly_targets', index=False)


def create_default_monthly_targets():
    """기본 월간 목표를 생성합니다 (최근 12개월)."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    current_date = datetime.now()
    months = []
    
    for i in range(-6, 6):  # 과거 6개월 ~ 미래 5개월
        month_date = current_date + relativedelta(months=i)
        months.append({
            'YearMonth': month_date.strftime('%Y-%m-01'),
            '목표매출': 50000000,  # 5천만원 기본값
            '예상매출': 48000000   # 4천8백만원 기본값
        })
    
    return pd.DataFrame(months)


def get_monthly_target(targets_df: pd.DataFrame, year_month: str) -> dict:
    """특정 월의 목표를 가져옵니다."""
    if targets_df is None or targets_df.empty:
        return {'목표매출': 50000000, '예상매출': 48000000}
    
    target_row = targets_df[targets_df['YearMonth'] == pd.to_datetime(year_month)]
    
    if target_row.empty:
        return {'목표매출': 50000000, '예상매출': 48000000}
    
    return {
        '목표매출': target_row.iloc[0]['목표매출'],
        '예상매출': target_row.iloc[0]['예상매출']
    }


def calculate_retention(df: pd.DataFrame, base_date: str, days: int, metric: str = 'DAU') -> float:
    """
    잔존율을 계산합니다.
    
    Args:
        df: 일일 데이터
        base_date: 기준 날짜
        days: D+N 일
        metric: 계산할 지표 (DAU, DBU, DRU)
    
    Returns:
        잔존율 (퍼센트)
    """
    try:
        base_date = pd.to_datetime(base_date)
        target_date = base_date + pd.Timedelta(days=days)
        
        base_value = df[df['Date'] == base_date][metric].values
        target_value = df[df['Date'] == target_date][metric].values
        
        if len(base_value) > 0 and len(target_value) > 0 and base_value[0] > 0:
            retention = (target_value[0] / base_value[0]) * 100
            return round(retention, 2)
        return 0.0
    except:
        return 0.0

