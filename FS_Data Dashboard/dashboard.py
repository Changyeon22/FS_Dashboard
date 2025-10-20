"""
FS 프로젝트 지표 대시보드 (고도화 버전)
웹 DB 기반 데이터 시각화
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from calendar import monthrange
from dotenv import load_dotenv
from config import PROJECTS, COUNTRY_NAMES, get_country_specific_config
from data_manager import load_daily_data, load_monthly_targets
from memo_handler import save_memo, delete_memo, get_memos, create_graph_memos_table
from exchange_rate_handler import get_exchange_rate, create_exchange_rate_table

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="FS 프로젝트 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    /* Streamlit 상단 메뉴 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Deploy 버튼과 Settings 버튼 숨기기 */
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] {display:none;}
    
    /* 메인 페이지 상단 여백 (1cm 간격) */
    .block-container {
        padding-top: 1cm !important;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    .stAppViewBlockContainer {
        padding-top: 1cm !important;
    }
    
    .main .block-container {
        padding-top: 1cm !important;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* 메인 컨텐츠 상단 여백 */
    .main .block-container > div {
        padding-top: 0rem;
    }
    
    /* 탭 상단 여백 제거 */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0rem;
    }
    
    /* 전체 페이지 상단 여백 제거 */
    .stApp > header {
        display: none;
    }
    
    /* 메인 컨텐츠 영역 최적화 */
    .main .block-container {
        max-width: 100%;
        padding-top: 1cm !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #1f77b4;
        letter-spacing: -0.01em;
        line-height: 1.3;
    }
    /* 메트릭 레이블 개선 */
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        letter-spacing: 0.025em !important;
        line-height: 1.4 !important;
    }
    /* 메트릭 값 개선 */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        color: #111827 !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        letter-spacing: -0.01em !important;
    }
    /* Delta 스타일 개선 */
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.025em !important;
    }
    /* 커스텀 메트릭 스타일 */
    .custom-metric {
        text-align: center;
        padding: 1rem;
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .custom-metric-label {
        font-size: 0.95rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.75rem;
        letter-spacing: 0.025em;
        line-height: 1.4;
    }
    .custom-metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #111827;
        line-height: 1.2;
        letter-spacing: -0.01em;
    }
    .metric-red {
        color: #dc3545 !important;
    }
    .metric-blue {
        color: #1f77b4 !important;
    }
    /* Delta 색상 커스터마이징 - 증가: 빨강, 감소: 파랑 */
    /* 감소시 SVG 화살표 색상 변경 */
    [data-testid="stMetricDelta"] svg[fill*="255, 43, 43"] {
        fill: #1f77b4 !important;
    }
    /* 감소시 텍스트 색상 변경 */
    [data-testid="stMetricDelta"][style*="rgb(255, 43, 43)"] {
        color: #1f77b4 !important;
    }
    /* 모든 빨간색 delta를 파란색으로 변경 (감소) */
    [data-testid="stMetricDelta"] {
        color: inherit;
    }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Down"]) {
        color: #1f77b4 !important;
    }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Down"]) svg {
        fill: #1f77b4 !important;
    }
    .metric-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .metric-table th, .metric-table td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    .metric-table th {
        background-color: #f0f2f6;
        font-weight: bold;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 탭 상단 여백 제거 */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.5rem !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] > div {
        padding-top: 0 !important;
    }
    
    /* 탭 컨테이너 여백 조정 */
    .stTabs {
        margin-top: -1rem !important;
    }
</style>
""", unsafe_allow_html=True)


def format_number(num):
    """숫자를 읽기 쉬운 형식으로 변환"""
    if pd.isna(num):
        return "0"
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"


def format_currency(amount):
    """통화 형식으로 변환 (천 단위 쉼표)"""
    if pd.isna(amount):
        return "₩0"
    return f"₩{amount:,.0f}"


def format_currency_full(amount):
    """통화 형식으로 변환 (전체 금액, 천 단위 쉼표)"""
    if pd.isna(amount):
        return "0"
    return f"{amount:,.0f}"


def get_month_range(date):
    """선택된 날짜의 월 초와 월 말 반환"""
    year = date.year
    month = date.month
    first_day = datetime(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num)
    return first_day, last_day


def calculate_daily_avg_sales(df, start_date, end_date):
    """기간 동안의 일평균 매출 계산"""
    period_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    if len(period_df) > 0:
        return period_df['일일매출'].mean()
    return 0


def tab_daily_metrics(df, selected_date, project, country):
    """탭 1: 일일지표"""
    
    # selected_date를 datetime으로 변환 (date 타입인 경우)
    if not isinstance(selected_date, datetime):
        selected_date = datetime.combine(selected_date, datetime.min.time())
    
    # 월 초와 월 말 계산
    month_start, month_end = get_month_range(selected_date)
    
    # 선택된 날짜의 데이터
    selected_date_pd = pd.to_datetime(selected_date)
    date_data = df[df['Date'] == selected_date_pd]
    
    if date_data.empty:
        st.warning(f"{selected_date.strftime('%Y-%m-%d')} 데이터가 없습니다.")
        return
    
    latest = date_data.iloc[0]
    
    # 월간 목표 데이터 로드
    targets_df = load_monthly_targets(project, country)
    year_month = f"{selected_date.year}-{selected_date.month:02d}-01"
    
    target_sales = 50000000  # 기본값
    if targets_df is not None and not targets_df.empty:
        target_row = targets_df[targets_df['YearMonth'] == pd.to_datetime(year_month)]
        if not target_row.empty:
            target_sales = target_row.iloc[0]['목표매출']
    
    # 기간 인식 매출 (월 초 ~ 선택된 날짜)
    month_df = df[(df['Date'] >= month_start) & (df['Date'] <= selected_date_pd)]
    period_sales = month_df['일일매출'].sum() if not month_df.empty else 0
    
    # 일평균 매출 (현재까지)
    avg_daily_sales = period_sales / len(month_df) if len(month_df) > 0 else 0
    
    # 남은 일수
    days_passed = (selected_date_pd - pd.to_datetime(month_start)).days + 1
    days_in_month = monthrange(selected_date.year, selected_date.month)[1]
    days_remaining = days_in_month - days_passed
    
    # 월간 예상 매출
    expected_remaining_sales = avg_daily_sales * days_remaining
    monthly_expected_sales = period_sales + expected_remaining_sales
    
    # 월간 공급가액 예상 매출 (부가세 제외)
    monthly_expected_supply = monthly_expected_sales / 1.1
    
    # 달성률 계산
    achievement_rate = (period_sales / target_sales * 100) if target_sales > 0 else 0
    expected_achievement_rate = (monthly_expected_supply / target_sales * 100) if target_sales > 0 else 0
    
    # ========================================
    # 섹션 1: 사업계획 달성 현황
    # ========================================
    st.markdown('<p class="section-header">사업계획 달성 현황</p>', unsafe_allow_html=True)
    
    # 국가별 사업계획 달성 현황 렌더링
    render_business_plan_metrics(project, country, selected_date, period_sales, target_sales, 
                                monthly_expected_sales, monthly_expected_supply, 
                                achievement_rate, expected_achievement_rate)
    
    st.markdown("---")
    
    # ========================================
    # 섹션 2: 매출 그래프
    # ========================================
    st.markdown('<p class="section-header">매출 그래프 (월간)</p>', unsafe_allow_html=True)
    
    # 해당 월의 모든 날짜 생성
    days_in_month = monthrange(selected_date.year, selected_date.month)[1]
    all_dates = [month_start + timedelta(days=i) for i in range(days_in_month)]
    
    # 실제 데이터와 예상 데이터 준비
    daily_target = target_sales / days_in_month
    target_sales_list = []
    actual_sales = []  # 발생 매출
    expected_sales = []  # 예상 매출
    
    for date in all_dates:
        date_pd = pd.to_datetime(date)
        day_data = df[df['Date'] == date_pd]
        
        # 목표 매출
        target_sales_list.append(daily_target)
        
        # 실제 매출 또는 예상 매출
        if date <= selected_date:
            # 선택된 날짜 이전 - 발생 매출
            if not day_data.empty:
                actual_sales.append(day_data.iloc[0]['일일매출'])
            else:
                actual_sales.append(0)
            expected_sales.append(None)
        else:
            # 선택된 날짜 이후 - 예상 매출
            actual_sales.append(None)
            expected_sales.append(avg_daily_sales)
    
    # 그래프 생성
    fig_sales = go.Figure()
    
    # 목표 매출 막대
    fig_sales.add_trace(go.Bar(
        x=all_dates,
        y=target_sales_list,
        name='목표 매출',
        marker_color='#ff7f0e',
        opacity=0.6
    ))
    
    # 발생 매출 막대
    fig_sales.add_trace(go.Bar(
        x=all_dates,
        y=actual_sales,
        name='발생 매출',
        marker_color='#1f77b4'
    ))
    
    # 예상 매출 (빨간색 테두리만, 내부 투명)
    fig_sales.add_trace(go.Bar(
        x=all_dates,
        y=expected_sales,
        name='예상 매출',
        marker=dict(
            color='rgba(220, 53, 69, 0.2)',  # 연한 빨간색 배경
            line=dict(color='#dc3545', width=2)  # 빨간색 테두리
        )
    ))
    
    # y축 범위 계산 (최대값보다 20% 더 크게)
    all_values = [v for v in target_sales_list + actual_sales + expected_sales if v is not None]
    max_value = max(all_values) if all_values else 1
    y_max = max_value * 1.2
    
    # 날짜 포맷 변경 (월/일 형식)
    formatted_dates = [f"{date.month}/{date.day}" for date in all_dates]
    
    # 주석(메모) 추가 - 사용자 입력 메모
    annotations = []
    
    # 색상 매핑
    color_map = {
        "빨간색": "#dc2626",
        "주황색": "#f59e0b", 
        "파란색": "#2563eb",
        "초록색": "#16a34a",
        "보라색": "#9333ea"
    }
    
    # DB에서 메모들을 조회하여 그래프에 표시
    memos = get_memos(project, country)
    for memo in memos:
        memo_date = pd.to_datetime(memo['date'])
        if memo_date in all_dates:
            # 해당 날짜의 최대 매출값 찾기
            event_idx = all_dates.index(memo_date)
            max_value_on_date = max(
                target_sales_list[event_idx] if target_sales_list[event_idx] is not None else 0,
                actual_sales[event_idx] if actual_sales[event_idx] is not None else 0,
                expected_sales[event_idx] if expected_sales[event_idx] is not None else 0
            )
            
            # 색상 선택
            arrow_color = color_map.get(memo['color'], "#dc2626")
            
            annotations.append(
                dict(
                    x=memo_date,
                    y=max_value_on_date + (y_max * 0.08),  # 막대 위쪽에 더 높이 표시
                    text=f"📝 {memo['text']}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,  # 화살표 크기 원래대로
                    arrowwidth=2,  # 화살표 두께 원래대로
                    arrowcolor=arrow_color,
                    ax=0,
                    ay=-30,  # 화살표 길이 원래대로
                    bgcolor="rgba(255,255,255,0.95)",  # 배경 투명도 증가
                    bordercolor=arrow_color,
                    borderwidth=2,  # 테두리 두께 증가
                    font=dict(size=16, color=arrow_color, family="Arial Black")  # 폰트 크기 더 증가
                )
            )
    
    fig_sales.update_layout(
        title=f"{selected_date.year}년 {selected_date.month}월 일별 매출",
            xaxis_title="날짜",
        yaxis_title="매출액 (원)",
            hovermode='x unified',
        height=600,  # 높이 증가
        template='plotly_white',
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        xaxis=dict(
            tickmode='array',
            tickvals=all_dates,
            ticktext=formatted_dates,
            tickangle=45,  # 날짜 라벨 회전
            tickfont=dict(style='normal')  # 이탤릭 제거
        ),
        yaxis=dict(
            tickformat=',',  # 쉼표로 숫자 표시
            separatethousands=True,
            range=[0, y_max]  # y축 범위 설정
        ),
        annotations=annotations  # 주석 추가
    )
    
    st.plotly_chart(fig_sales, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # 섹션 3: 주요 지표 정리
    # ========================================
    st.markdown('<p class="section-header">주요 지표 ({})  </p>'.format(selected_date.strftime('%Y-%m-%d')), unsafe_allow_html=True)
    
    # 전날 데이터 가져오기
    prev_date = selected_date_pd - timedelta(days=1)
    prev_data = df[df['Date'] == prev_date]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        current_dau = latest.get('DAU', 0)
        if not prev_data.empty:
            prev_dau = prev_data.iloc[0].get('DAU', 0)
            delta_dau = current_dau - prev_dau
            st.metric("DAU", format_number(current_dau), 
                     delta=f"{delta_dau:+,}",
                     delta_color="normal" if delta_dau >= 0 else "inverse")
        else:
            st.metric("DAU", format_number(current_dau))
    
    with col2:
        current_dru = latest.get('DRU', 0)
        if not prev_data.empty:
            prev_dru = prev_data.iloc[0].get('DRU', 0)
            delta_dru = current_dru - prev_dru
            st.metric("DRU", format_number(current_dru),
                     delta=f"{delta_dru:+,}",
                     delta_color="normal" if delta_dru >= 0 else "inverse")
        else:
            st.metric("DRU", format_number(current_dru))
    
    with col3:
        current_dbu = latest.get('DBU', 0)
        if not prev_data.empty:
            prev_dbu = prev_data.iloc[0].get('DBU', 0)
            delta_dbu = current_dbu - prev_dbu
            st.metric("DBU", format_number(current_dbu),
                     delta=f"{delta_dbu:+,}",
                     delta_color="normal" if delta_dbu >= 0 else "inverse")
        else:
            st.metric("DBU", format_number(current_dbu))
    
    with col4:
        current_pu = latest.get('PU', 0)
        if not prev_data.empty:
            prev_pu = prev_data.iloc[0].get('PU', 0)
            delta_pu = current_pu - prev_pu
            st.metric("PU", format_number(current_pu),
                     delta=f"{delta_pu:+,}",
                     delta_color="normal" if delta_pu >= 0 else "inverse")
        else:
            st.metric("PU", format_number(current_pu))
    
    with col5:
        current_sales = latest.get('일일매출', 0)
        if not prev_data.empty:
            prev_sales = prev_data.iloc[0].get('일일매출', 0)
            delta_sales = current_sales - prev_sales
            st.metric("일일 매출", format_currency_full(current_sales),
                     delta=format_currency_full(delta_sales),
                     delta_color="normal" if delta_sales >= 0 else "inverse")
        else:
            st.metric("일일 매출", format_currency_full(current_sales))
    
    # 환율 정보 표시 (해외 프로젝트인 경우)
    if country in ['CHN', 'SEA', 'GSP']:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-header">환율 정보</p>', unsafe_allow_html=True)
        
        # 해당 날짜의 환율 조회
        exchange_rate = get_exchange_rate(selected_date.strftime('%Y-%m-%d'))
        
        if exchange_rate:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("USD/KRW", f"{exchange_rate['usd_krw']:,.2f}")
            with col2:
                st.metric("CNY/KRW", f"{exchange_rate['cny_krw']:,.2f}")
        else:
            st.info("해당 날짜의 환율 정보가 없습니다.")
    
    st.markdown("---")
    
    # ========================================
    # 섹션 4: 지표 현황 (30일)
    # ========================================
    st.markdown('<p class="section-header">지표 현황 (최근 30일)</p>', unsafe_allow_html=True)
    
    # 30일 데이터
    date_30_days_ago = selected_date_pd - timedelta(days=29)
    period_30_df = df[(df['Date'] >= date_30_days_ago) & (df['Date'] <= selected_date_pd)].copy()
    
    if not period_30_df.empty:
        # 날짜 포맷 변경
        period_30_df['Date'] = period_30_df['Date'].dt.strftime('%Y-%m-%d')
        
        # 슬라이드 바 없이 전체 데이터 표시
        st.dataframe(
            period_30_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("최근 30일 데이터가 없습니다.")


def tab_user_trends(df, selected_date):
    """탭 2: 유저 동향 및 이슈 보고 (준비 중)"""
    st.info("유저 동향 및 이슈 보고 탭은 준비 중입니다.")


def tab_data_copy(df, selected_date, project, country):
    """탭 3: 데이터 복사용 표"""
    st.markdown('<p class="section-header">데이터 복사용 표</p>', unsafe_allow_html=True)
    
    # 기준 날짜로부터 30일 전까지의 데이터 준비
    selected_date_pd = pd.to_datetime(selected_date)
    month_start = selected_date_pd - timedelta(days=29)  # 30일 전
    month_end = selected_date_pd  # 기준 날짜까지
    
    # 30일 데이터 필터링
    month_df = df[(df['Date'] >= month_start) & (df['Date'] <= month_end)].copy()
    
    if month_df.empty:
        st.warning("30일치 데이터가 없습니다.")
        return
    
    # 날짜 순으로 정렬 (최신 날짜가 위로)
    month_df = month_df.sort_values('Date', ascending=False)
    
    # 월간 목표 데이터 로드
    targets_df = load_monthly_targets(project, country)
    
    # 사업계획 달성 현황 지표 계산
    achievement_data = []
    
    for _, row in month_df.iterrows():
        date = row['Date']
        year_month = f"{date.year}-{date.month:02d}-01"
        
        # 월간 목표
        target_sales = 50000000  # 기본값
        if targets_df is not None and not targets_df.empty:
            target_row = targets_df[targets_df['YearMonth'] == pd.to_datetime(year_month)]
            if not target_row.empty:
                target_sales = target_row.iloc[0]['목표매출']
        
        # 기간 인식 매출 (월 초 ~ 해당 날짜)
        month_start_calc = pd.to_datetime(f"{date.year}-{date.month:02d}-01")
        month_data_calc = df[(df['Date'] >= month_start_calc) & (df['Date'] <= date)]
        period_sales = month_data_calc['일일매출'].sum() if not month_data_calc.empty else 0
        
        # 일평균 매출
        avg_daily_sales = period_sales / len(month_data_calc) if len(month_data_calc) > 0 else 0
        
        # 남은 일수
        days_passed = (date - month_start_calc).days + 1
        days_in_month = monthrange(date.year, date.month)[1]
        days_remaining = days_in_month - days_passed
        
        # 월간 예상 매출
        expected_remaining_sales = avg_daily_sales * days_remaining
        monthly_expected_sales = period_sales + expected_remaining_sales
        
        # 월간 공급가액 예상 매출
        monthly_expected_supply = monthly_expected_sales / 1.1
        
        # 달성률
        achievement_rate = (period_sales / target_sales * 100) if target_sales > 0 else 0
        expected_achievement_rate = (monthly_expected_supply / target_sales * 100) if target_sales > 0 else 0
        
        achievement_data.append({
            '날짜': date.strftime('%Y-%m-%d'),
            '월간 사업계획 공급가액 목표': f"{target_sales:,.0f}",
            '기간 인식 매출': f"{period_sales:,.0f}",
            '월간 사업계획 달성률': f"{achievement_rate:.1f}%",
            '월간 예상 매출': f"{monthly_expected_sales:,.0f}",
            '월간 공급가액 예상 매출': f"{monthly_expected_supply:,.0f}",
            '예상 사업계획 달성률': f"{expected_achievement_rate:.1f}%"
        })
    
    # 사업계획 달성 현황 표
    st.subheader("사업계획 달성 현황 (30일)")
    achievement_df = pd.DataFrame(achievement_data)
    st.dataframe(achievement_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 지표 현황 표
    st.subheader("지표 현황 (30일)")
    
    # 지표 데이터 준비
    metrics_data = []
    for _, row in month_df.iterrows():
        metrics_data.append({
            '날짜': row['Date'].strftime('%Y-%m-%d'),
            'DAU': f"{row.get('DAU', 0):,}",
            'DRU': f"{row.get('DRU', 0):,}",
            'DBU': f"{row.get('DBU', 0):,}",
            'PU': f"{row.get('PU', 0):,}",
            '일일매출': f"{row.get('일일매출', 0):,}",
            'PC방매출': f"{row.get('PC방매출', 0):,}",
            '평균동접': f"{row.get('평균동접', 0):,}",
            '최대동접': f"{row.get('최대동접', 0):,}",
            '플레이판수': f"{row.get('플레이판수', 0):,}",
            '플레이타임': f"{row.get('플레이타임', 0):,}"
        })
    
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)


def tab_others(df, selected_date):
    """탭 4: 기타 (준비 중)"""
    st.info("기타 탭은 준비 중입니다.")


def main():
    # 사이드바 - 프로젝트 및 국가 선택
    with st.sidebar:
        st.header("설정")
        
        # 프로젝트 선택
        project_list = list(PROJECTS.keys())
        selected_project = st.selectbox(
            "프로젝트",
            project_list
        )
        
        # 국가 선택
        available_countries = PROJECTS[selected_project]['countries']
        selected_country = st.selectbox(
            "국가/지역",
            available_countries,
            format_func=lambda x: COUNTRY_NAMES.get(x, x)
        )
        
        st.markdown("---")
        
        # 날짜 선택
        st.subheader("날짜 선택")
        selected_date = st.date_input(
            "기준 날짜",
            value=datetime(2022, 2, 15)
        )
        
        st.markdown("---")
        
        # 메모 관리 섹션
        st.subheader("📝 그래프 메모 관리")
        
        # 메모용 프로젝트/국가 선택
        memo_project = st.selectbox(
            "메모 프로젝트",
            project_list,
            index=project_list.index(selected_project),
            help="메모를 추가할 프로젝트를 선택하세요"
        )
        
        memo_countries = PROJECTS[memo_project]['countries']
        memo_country = st.selectbox(
            "메모 국가/지역",
            memo_countries,
            index=memo_countries.index(selected_country),
            format_func=lambda x: COUNTRY_NAMES.get(x, x),
            help="메모를 추가할 국가를 선택하세요"
        )
        
        # 메모 입력
        memo_date = st.date_input(
            "메모 날짜",
            value=selected_date,
            help="메모를 추가할 날짜를 선택하세요"
        )
        
        memo_text = st.text_input(
            "메모 내용",
            placeholder="예: 대규모 이벤트, 서버 점검, 업데이트 등",
            help="해당 날짜에 표시할 메모를 입력하세요"
        )
        
        memo_color = st.selectbox(
            "메모 색상",
            options=["빨간색", "주황색", "파란색", "초록색", "보라색"],
            index=0,
            help="메모의 색상을 선택하세요"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("메모 추가", type="primary"):
                if memo_text.strip():
                    # DB에 메모 저장
                    if save_memo(memo_project, memo_country, memo_date.strftime('%Y-%m-%d'), memo_text, memo_color):
                        st.success(f"메모가 저장되었습니다: {memo_project}-{memo_country} {memo_date.strftime('%Y-%m-%d')}")
                        st.rerun()  # 페이지 새로고침
                    else:
                        st.error("메모 저장에 실패했습니다.")
                else:
                    st.error("메모 내용을 입력해주세요.")
        
        with col2:
            if st.button("메모 삭제"):
                if delete_memo(memo_project, memo_country, memo_date.strftime('%Y-%m-%d')):
                    st.success("메모가 삭제되었습니다.")
                    st.rerun()  # 페이지 새로고침
                else:
                    st.warning("삭제할 메모가 없거나 삭제에 실패했습니다.")
        
        # 현재 메모 목록 표시
        current_memos = get_memos(memo_project, memo_country)
        if current_memos:
            st.markdown("**현재 메모 목록:**")
            for memo in current_memos:
                st.text(f"📅 {memo['date']}: {memo['text']} ({memo['color']})")
    
    # 데이터 로드 (전체 기간)
    df = load_daily_data(selected_project, selected_country)
    
    if df is None or df.empty:
        country_name_clean = COUNTRY_NAMES.get(selected_country, selected_country)
        st.warning(f"{selected_project} - {country_name_clean} 데이터가 없습니다.")
        st.info("데이터를 수집하려면: `python data_collector.py`")
        return
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs([
        "일일지표",
        "유저 동향 및 이슈 보고", 
        "데이터 복사",
        "기타"
    ])
    
    with tab1:
        tab_daily_metrics(df, selected_date, selected_project, selected_country)
    
    with tab2:
        tab_user_trends(df, selected_date)
    
    with tab3:
        tab_data_copy(df, selected_date, selected_project, selected_country)
    
    with tab4:
        tab_others(df, selected_date)


def render_business_plan_metrics(project, country, selected_date, period_sales, target_sales, 
                                monthly_expected_sales, monthly_expected_supply, 
                                achievement_rate, expected_achievement_rate):
    """국가별 사업계획 달성 현황 렌더링"""
    
    # 국가별 설정 가져오기
    country_config = get_country_specific_config(project, country)
    business_format = country_config.get('business_plan_format', 'default')
    
    country_name_clean = COUNTRY_NAMES.get(country, country)
    
    if business_format == 'fs1_sea':  # FS1 한국, FS1 동남아시아
        render_fs1_sea_format(project, country, country_name_clean, selected_date, 
                             period_sales, target_sales, monthly_expected_sales, 
                             monthly_expected_supply, achievement_rate, expected_achievement_rate)
    
    elif business_format == 'fs1_chn':  # FS1 중국
        render_fs1_chn_format(project, country, country_name_clean, selected_date, 
                             period_sales, target_sales, monthly_expected_sales, 
                             monthly_expected_supply, achievement_rate, expected_achievement_rate)
    
    elif business_format == 'fs2_kor':  # FS2 한국
        render_fs2_kor_format(project, country, country_name_clean, selected_date, 
                             period_sales, target_sales, monthly_expected_sales, 
                             monthly_expected_supply, achievement_rate, expected_achievement_rate)
    
    elif business_format == 'fs2_chn':  # FS2 중국
        render_fs2_chn_format(project, country, country_name_clean, selected_date, 
                             period_sales, target_sales, monthly_expected_sales, 
                             monthly_expected_supply, achievement_rate, expected_achievement_rate)
    
    elif business_format == 'fs2_gsp':  # FS2 글로벌
        render_fs2_gsp_format(project, country, country_name_clean, selected_date, 
                             period_sales, target_sales, monthly_expected_sales, 
                             monthly_expected_supply, achievement_rate, expected_achievement_rate)
    
    else:  # 기본 양식
        render_default_format(project, country, country_name_clean, selected_date, 
                             period_sales, target_sales, monthly_expected_sales, 
                             monthly_expected_supply, achievement_rate, expected_achievement_rate)


def render_fs1_sea_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate):
    """FS1 동남아시아 양식 (FS1 한국도 동일)"""
    # 첫 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">프로젝트</div>
            <div class="custom-metric-value">{project} - {country_name_clean}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 공급가액 목표</div>
            <div class="custom-metric-value">{format_currency(target_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 인식 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        achievement_color = "metric-red" if achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 두 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기준 날짜</div>
            <div class="custom-metric-value">{selected_date.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 공급가액 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_supply)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        expected_color = "metric-red" if expected_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)


def render_fs1_chn_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate):
    """FS1 중국 양식"""
    # 캐시 컨슘 관련 계산 (임의 데이터)
    cash_consumption_target = target_sales * 0.3  # 목표의 30%로 임의 설정
    cash_consumption_period = period_sales * 0.3  # 기간 매출의 30%
    cash_consumption_expected = monthly_expected_sales * 0.3  # 예상 매출의 30%
    cash_achievement_rate = (cash_consumption_period / cash_consumption_target * 100) if cash_consumption_target > 0 else 0
    cash_expected_rate = (cash_consumption_expected / cash_consumption_target * 100) if cash_consumption_target > 0 else 0
    
    # 첫 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">프로젝트</div>
            <div class="custom-metric-value">{project} - {country_name_clean}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 목표</div>
            <div class="custom-metric-value">{format_currency(target_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 인식 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        achievement_color = "metric-red" if achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">인식 매출 목표 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 두 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기준 날짜</div>
            <div class="custom-metric-value">{selected_date.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 인식 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        expected_color = "metric-red" if expected_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">캐시 컨슘 목표</div>
            <div class="custom-metric-value">{format_currency(cash_consumption_target)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 세 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 캐시 매출</div>
            <div class="custom-metric-value">{format_currency(cash_consumption_period)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        cash_achievement_color = "metric-red" if cash_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">캐시 컨슘 목표 달성률</div>
            <div class="custom-metric-value {cash_achievement_color}">{cash_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 캐시 매출</div>
            <div class="custom-metric-value">{format_currency(cash_consumption_expected)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        cash_expected_color = "metric-red" if cash_expected_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 캐시 컨슘 목표 달성률</div>
            <div class="custom-metric-value {cash_expected_color}">{cash_expected_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)


def render_fs2_kor_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate):
    """FS2 한국 양식"""
    # 첫 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">프로젝트</div>
            <div class="custom-metric-value">{project} - {country_name_clean}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 목표</div>
            <div class="custom-metric-value">{format_currency(target_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        achievement_color = "metric-red" if achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 두 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기준 날짜</div>
            <div class="custom-metric-value">{selected_date.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        expected_color = "metric-red" if expected_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">공급가액: 기간 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_supply)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 세 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">공급가액: 월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">공급가액: 월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_supply)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">공급가액: 예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">-</div>
            <div class="custom-metric-value">-</div>
        </div>
        """, unsafe_allow_html=True)


def render_fs2_chn_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate):
    """FS2 중국 양식"""
    # 환율 정보 가져오기
    exchange_rates = get_exchange_rate(selected_date.strftime('%Y-%m-%d'))
    exchange_rate_usd = exchange_rates.get('USD', 1300.0) if exchange_rates else 1300.0
    exchange_rate_cny = exchange_rates.get('CNY', 180.0) if exchange_rates else 180.0
    
    # 캐시 컨슘 계산 (매출/35*100)
    cash_consumption_period = period_sales / 35 * 100
    cash_consumption_expected = monthly_expected_sales / 35 * 100
    cash_achievement_rate = (cash_consumption_period / target_sales * 100) if target_sales > 0 else 0
    cash_expected_rate = (cash_consumption_expected / target_sales * 100) if target_sales > 0 else 0
    
    # 첫 번째 행 - 인식 매출
    st.markdown("**인식 매출**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">프로젝트</div>
            <div class="custom-metric-value">{project} - {country_name_clean}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 목표</div>
            <div class="custom-metric-value">{format_currency(target_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        achievement_color = "metric-red" if achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기준 날짜</div>
            <div class="custom-metric-value">{selected_date.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        expected_color = "metric-red" if expected_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">-</div>
            <div class="custom-metric-value">-</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 두 번째 행 - 환율 적용
    st.markdown("**환율 적용**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">환율(달러, 위안화)</div>
            <div class="custom-metric-value">USD: {exchange_rate_usd:.2f}<br/>CNY: {exchange_rate_cny:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">-</div>
            <div class="custom-metric-value">-</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">-</div>
            <div class="custom-metric-value">-</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">-</div>
            <div class="custom-metric-value">-</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 세 번째 행 - 캐시 컨슘
    st.markdown("**캐시 컨슘**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 매출</div>
            <div class="custom-metric-value">{format_currency(cash_consumption_period)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        cash_achievement_color = "metric-red" if cash_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {cash_achievement_color}">{cash_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(cash_consumption_expected)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        cash_expected_color = "metric-red" if cash_expected_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {cash_expected_color}">{cash_expected_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)


def render_fs2_gsp_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate):
    """FS2 글로벌 양식"""
    # 환율 정보 가져오기
    exchange_rates = get_exchange_rate(selected_date.strftime('%Y-%m-%d'))
    exchange_rate_usd = exchange_rates.get('USD', 1300.0) if exchange_rates else 1300.0
    
    # 첫 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">프로젝트</div>
            <div class="custom-metric-value">{project} - {country_name_clean}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 목표</div>
            <div class="custom-metric-value">{format_currency(target_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        achievement_color = "metric-red" if achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 두 번째 행
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기준 날짜</div>
            <div class="custom-metric-value">{selected_date.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        expected_color = "metric-red" if expected_achievement_rate >= 100 else "metric-blue"
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">환율(달러)</div>
            <div class="custom-metric-value">{exchange_rate_usd:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 세 번째 행 - 환율 적용
    st.markdown("**환율 적용**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">기간 매출</div>
            <div class="custom-metric-value">{format_currency(period_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 사업계획 달성률</div>
            <div class="custom-metric-value {achievement_color}">{achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">월간 예상 매출</div>
            <div class="custom-metric-value">{format_currency(monthly_expected_sales)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-metric">
            <div class="custom-metric-label">예상 사업계획 달성률</div>
            <div class="custom-metric-value {expected_color}">{expected_achievement_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)


def render_default_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate):
    """기본 양식 (기존과 동일)"""
    render_fs1_sea_format(project, country, country_name_clean, selected_date, 
                         period_sales, target_sales, monthly_expected_sales, 
                         monthly_expected_supply, achievement_rate, expected_achievement_rate)


if __name__ == "__main__":
    main()
