"""
프로젝트 및 국가 설정 파일
"""
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 및 국가 설정
PROJECTS = {
    'FS1': {
        'name': 'FS1',
        'countries': ['KOR', 'CHN', 'SEA']
    },
    'FS2': {
        'name': 'FS2',
        'countries': ['KOR', 'CHN', 'GSP']
    }
}

# 국가명 표시
COUNTRY_NAMES = {
    'KOR': 'KOR',
    'CHN': 'CHN',
    'SEA': 'SEA',
    'GSP': 'GSP'
}

# 지표 한글명 매핑
METRIC_NAMES = {
    'dau': 'DAU',
    'dru': 'DRU', 
    'dbu': 'DBU',
    'sales': '일일매출',
    'pc_room_sales': 'PC방매출',
    'pu': 'PU',
    'avg_concurrent': '평균동접',
    'max_concurrent': '최대동접',
    'play_rounds': '플레이판수',
    'play_time_minutes': '플레이타임'
}


def get_data_path(project: str, country: str) -> str:
    """
    프로젝트와 국가에 따른 데이터 파일 경로를 반환합니다.
    (레거시 엑셀 파일용)
    """
    return f"data/{project}/{country}/daily_metrics.xlsx"


def get_backup_db_name(project: str, country: str) -> str:
    """
    프로젝트와 국가에 따른 게임 백업 DB 이름을 반환합니다.
    
    Args:
        project: 프로젝트명 (예: 'FS1')
        country: 국가코드 (예: 'KOR')
    
    Returns:
        str: DB 이름 (환경 변수에서 가져옴)
    """
    # 환경 변수 확인
    db_key = f"BACKUP_DB_{project}_{country}"
    db_name = os.getenv(db_key)
    
    if db_name:
        return db_name
    
    # 환경 변수가 없으면 모든 국가를 BIWORK 사용 (나중에 실제 DB로 변경)
    return 'BIWORK'


def get_country_specific_config(project: str, country: str) -> dict:
    """
    국가별 특정 설정을 반환합니다.
    
    Args:
        project: 프로젝트명
        country: 국가코드
    
    Returns:
        dict: 국가별 설정
    """
    # 기본 설정
    config = {
        'db_name': get_backup_db_name(project, country),
        'table_name': 'DailyStatistics_New',  # 기본 테이블
        'currency': 'KRW',  # 기본 통화
        'timezone': 'Asia/Seoul',  # 기본 시간대
        'exchange_rate_needed': False,  # 환율 필요 여부
        'business_plan_format': 'default'  # 사업계획 달성 현황 양식
    }
    
    # 국가별 특수 설정
    if country in ['CHN', 'SEA', 'GSP']:
        config['exchange_rate_needed'] = True
        if country == 'CHN':
            config['currency'] = 'CNY'
        elif country == 'SEA':
            config['currency'] = 'USD'
        elif country == 'GSP':
            config['currency'] = 'USD'
    
    # 사업계획 달성 현황 양식 설정
    if project == 'FS1':
        if country == 'KOR':
            config['business_plan_format'] = 'fs1_sea'  # FS1 동남아시아와 동일
        elif country == 'CHN':
            config['business_plan_format'] = 'fs1_chn'  # FS1 중국 전용
        elif country == 'SEA':
            config['business_plan_format'] = 'fs1_sea'  # FS1 동남아시아 기본
    elif project == 'FS2':
        if country == 'KOR':
            config['business_plan_format'] = 'fs2_kor'  # FS2 한국 전용
        elif country == 'CHN':
            config['business_plan_format'] = 'fs2_chn'  # FS2 중국 전용
        elif country == 'GSP':
            config['business_plan_format'] = 'fs2_gsp'  # FS2 글로벌 전용
    
    return config


def get_all_project_country_combinations():
    """모든 프로젝트-국가 조합을 반환합니다."""
    combinations = []
    for project, config in PROJECTS.items():
        for country in config['countries']:
            combinations.append((project, country))
    return combinations


def get_display_metric_name(metric_key: str) -> str:
    """
    지표 키를 표시용 이름으로 변환합니다.
    
    Args:
        metric_key: 지표 키 (예: 'dau')
    
    Returns:
        str: 표시용 이름 (예: 'DAU')
    """
    return METRIC_NAMES.get(metric_key, metric_key)

