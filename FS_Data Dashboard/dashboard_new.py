"""
FS 프로젝트 지표 대시보드 (신규 버전)
웹 DB 기반 데이터 시각화
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import PROJECTS, COUNTRY_NAMES
from data_manager import load_daily_data, load_monthly_targets

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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def format_number(num):
    """숫자를 읽기 쉬운 형식으로 변환"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"


def format_currency(amount):
    """통화 형식으로 변환"""
    if amount >= 100_000_000:
        return f"₩{amount/100_000_000:.1f}억"
    elif amount >= 10_000:
        return f"₩{amount/10_000:.0f}만"
    else:
        return f"₩{amount:,.0f}"


def main():
    # 헤더
    st.markdown('<p class="main-header">📊 FS 프로젝트 대시보드</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 사이드바 - 프로젝트 및 국가 선택
    with st.sidebar:
        st.header("🎯 설정")
        
        # 프로젝트 선택
        project_list = list(PROJECTS.keys())
        selected_project = st.selectbox(
            "프로젝트",
            project_list,
            format_func=lambda x: f"📁 {x}"
        )
        
        # 국가 선택
        available_countries = PROJECTS[selected_project]['countries']
        selected_country = st.selectbox(
            "국가/지역",
            available_countries,
            format_func=lambda x: COUNTRY_NAMES.get(x, x)
        )
        
        st.markdown("---")
        
        # 날짜 범위 선택
        st.subheader("📅 날짜 범위")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "시작일",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "종료일",
                value=datetime.now()
            )
        
        st.markdown("---")
        
        # 선택 정보 표시
        st.info(f"""
        **현재 선택:**
        
        📁 프로젝트: {selected_project}
        
        🌍 국가: {COUNTRY_NAMES.get(selected_country, selected_country)}
        
        📅 기간: {start_date} ~ {end_date}
        """)
    
    # 데이터 로드
    df = load_daily_data(
        selected_project, 
        selected_country,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if df is None or df.empty:
        st.warning(f"⚠️ {selected_project} - {COUNTRY_NAMES.get(selected_country)} 데이터가 없습니다.")
        st.info("💡 데이터를 수집하려면: `python data_collector.py`")
        return
    
    # 최신 데이터 (마지막 행)
    latest = df.iloc[-1]
    latest_date = latest['Date'].strftime('%Y-%m-%d') if hasattr(latest['Date'], 'strftime') else str(latest['Date'])
    
    # 헤더 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 프로젝트", selected_project)
    with col2:
        st.metric("🌍 국가", COUNTRY_NAMES.get(selected_country, selected_country))
    with col3:
        st.metric("📅 최신 데이터", latest_date)
    with col4:
        st.metric("📊 데이터 수", f"{len(df)}일")
    
    st.markdown("---")
    
    # 1. 주요 KPI 카드
    st.subheader("📈 주요 지표 (최신)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        dau = latest.get('DAU', 0)
        st.metric(
            "DAU",
            format_number(dau),
            help="Daily Active Users - 일일 활성 유저"
        )
    
    with col2:
        dru = latest.get('DRU', 0)
        st.metric(
            "DRU",
            format_number(dru),
            help="Daily Register Users - 일일 신규 유저"
        )
    
    with col3:
        dbu = latest.get('DBU', 0)
        st.metric(
            "DBU",
            format_number(dbu),
            help="Daily Back Users - 일일 복귀 유저"
        )
    
    with col4:
        pu = latest.get('PU', 0)
        st.metric(
            "PU",
            format_number(pu),
            help="Purchase Users - 구매 유저"
        )
    
    with col5:
        sales = latest.get('일일매출', 0)
        st.metric(
            "일일 매출",
            format_currency(sales),
            help="Daily Sales"
        )
    
    st.markdown("---")
    
    # 2. 동접 및 플레이 지표
    st.subheader("🎮 플레이 지표 (최신)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        acu = latest.get('평균동접', 0)
        st.metric(
            "평균 동접",
            format_number(acu),
            help="Average Current Users"
        )
    
    with col2:
        mcu = latest.get('최대동접', 0)
        st.metric(
            "최대 동접",
            format_number(mcu),
            help="Maximum Current Users"
        )
    
    with col3:
        play_rounds = latest.get('플레이판수', 0)
        st.metric(
            "평균 플레이 판수",
            f"{play_rounds:.1f}",
            help="Average Play Count"
        )
    
    with col4:
        play_time = latest.get('플레이타임', 0)
        st.metric(
            "평균 플레이 타임",
            f"{play_time:.0f}분",
            help="Average Play Time (minutes)"
        )
    
    st.markdown("---")
    
    # 3. 시계열 차트 - 유저 지표
    st.subheader("📊 유저 지표 추이")
    
    fig_users = go.Figure()
    
    fig_users.add_trace(go.Scatter(
        x=df['Date'],
        y=df['DAU'],
        mode='lines+markers',
        name='DAU',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    fig_users.add_trace(go.Scatter(
        x=df['Date'],
        y=df['DRU'],
        mode='lines+markers',
        name='DRU',
        line=dict(color='#ff7f0e', width=2),
        marker=dict(size=6)
    ))
    
    fig_users.add_trace(go.Scatter(
        x=df['Date'],
        y=df['DBU'],
        mode='lines+markers',
        name='DBU',
        line=dict(color='#2ca02c', width=2),
        marker=dict(size=6)
    ))
    
    fig_users.update_layout(
        title="일일 유저 지표",
        xaxis_title="날짜",
        yaxis_title="유저 수",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_users, use_container_width=True)
    
    # 4. 시계열 차트 - 매출 및 구매 유저
    st.subheader("💰 매출 및 구매 유저 추이")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_sales = go.Figure()
        fig_sales.add_trace(go.Bar(
            x=df['Date'],
            y=df['일일매출'],
            name='일일 매출',
            marker_color='#d62728'
        ))
        fig_sales.update_layout(
            title="일일 매출",
            xaxis_title="날짜",
            yaxis_title="매출 (원)",
            height=350,
            template='plotly_white'
        )
        st.plotly_chart(fig_sales, use_container_width=True)
    
    with col2:
        fig_pu = go.Figure()
        fig_pu.add_trace(go.Scatter(
            x=df['Date'],
            y=df['PU'],
            mode='lines+markers',
            name='PU',
            line=dict(color='#9467bd', width=2),
            marker=dict(size=6),
            fill='tozeroy'
        ))
        fig_pu.update_layout(
            title="구매 유저 (PU)",
            xaxis_title="날짜",
            yaxis_title="유저 수",
            height=350,
            template='plotly_white'
        )
        st.plotly_chart(fig_pu, use_container_width=True)
    
    # 5. 시계열 차트 - 동접
    st.subheader("👥 동시 접속 유저 추이")
    
    fig_concurrent = go.Figure()
    
    fig_concurrent.add_trace(go.Scatter(
        x=df['Date'],
        y=df['최대동접'],
        mode='lines+markers',
        name='최대 동접 (MCU)',
        line=dict(color='#e377c2', width=2),
        marker=dict(size=6)
    ))
    
    fig_concurrent.add_trace(go.Scatter(
        x=df['Date'],
        y=df['평균동접'],
        mode='lines+markers',
        name='평균 동접 (ACU)',
        line=dict(color='#7f7f7f', width=2),
        marker=dict(size=6)
    ))
    
    fig_concurrent.update_layout(
        title="동시 접속 유저",
        xaxis_title="날짜",
        yaxis_title="유저 수",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_concurrent, use_container_width=True)
    
    # 6. 시계열 차트 - 플레이 지표
    st.subheader("🎮 플레이 지표 추이")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_rounds = go.Figure()
        fig_rounds.add_trace(go.Scatter(
            x=df['Date'],
            y=df['플레이판수'],
            mode='lines+markers',
            name='평균 플레이 판수',
            line=dict(color='#bcbd22', width=2),
            marker=dict(size=6)
        ))
        fig_rounds.update_layout(
            title="평균 플레이 판수",
            xaxis_title="날짜",
            yaxis_title="판수",
            height=350,
            template='plotly_white'
        )
        st.plotly_chart(fig_rounds, use_container_width=True)
    
    with col2:
        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(
            x=df['Date'],
            y=df['플레이타임'],
            mode='lines+markers',
            name='평균 플레이 타임',
            line=dict(color='#17becf', width=2),
            marker=dict(size=6)
        ))
        fig_time.update_layout(
            title="평균 플레이 타임 (분)",
            xaxis_title="날짜",
            yaxis_title="시간 (분)",
            height=350,
            template='plotly_white'
        )
        st.plotly_chart(fig_time, use_container_width=True)
    
    st.markdown("---")
    
    # 7. 통계 요약
    st.subheader("📊 기간 통계 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "평균 DAU",
            format_number(df['DAU'].mean()),
            help=f"최소: {format_number(df['DAU'].min())}, 최대: {format_number(df['DAU'].max())}"
        )
    
    with col2:
        st.metric(
            "총 매출",
            format_currency(df['일일매출'].sum()),
            help=f"평균: {format_currency(df['일일매출'].mean())}"
        )
    
    with col3:
        st.metric(
            "평균 PU",
            format_number(df['PU'].mean()),
            help=f"총 구매 유저 평균"
        )
    
    with col4:
        conversion_rate = (df['PU'].sum() / df['DAU'].sum() * 100) if df['DAU'].sum() > 0 else 0
        st.metric(
            "평균 전환율",
            f"{conversion_rate:.2f}%",
            help="PU / DAU 비율"
        )
    
    st.markdown("---")
    
    # 8. 상세 데이터 테이블
    with st.expander("📋 상세 데이터 보기"):
        st.dataframe(
            df.style.format({
                'Date': lambda x: x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x),
                'DAU': '{:,.0f}',
                'DRU': '{:,.0f}',
                'DBU': '{:,.0f}',
                'PU': '{:,.0f}',
                '일일매출': '₩{:,.0f}',
                '평균동접': '{:,.0f}',
                '최대동접': '{:,.0f}',
                '플레이판수': '{:.1f}',
                '플레이타임': '{:.0f}'
            }),
            use_container_width=True,
            height=400
        )


if __name__ == "__main__":
    main()

