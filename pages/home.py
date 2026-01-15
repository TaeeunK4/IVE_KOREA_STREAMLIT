# =============================================================================
# 광고 데이터 정보 페이지
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import boto3
from io import BytesIO

# =============================================================================
# CSS 설정
# =============================================================================

CARD_STYLE = """
padding:16px;
border-radius:12px;
box-shadow: 0 4px 12px rgba(0,0,0,0.1);
background-color:#ffffff;
margin-bottom:16px;
"""

TITLE_STYLE = "margin-bottom:8px; color:#333;"
VALUE_STYLE = "margin:0; color:#111; font-size:24px; font-weight:bold;"

st.markdown("""
<style>

/* ==============================
   3D 카드 스타일 (메인 컨테이너용)
============================== */
.card-3d {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px;
    width: 100%;
    box-shadow:
        0 4px 8px rgba(0,0,0,0.04),
        0 12px 24px rgba(0,0,0,0.08);
    border: 1px solid #F1F3F5;
}

/* ==============================
   KPI 카드 스타일
============================== */
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 20px;
    width: 100%;
    box-shadow:
        0 4px 10px rgba(0,0,0,0.05),
        0 12px 28px rgba(0,0,0,0.08);
    border: 1px solid #E5E7EB;
}

.kpi-title {
    font-size: 14px;
    color: #6B7280;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
}

.kpi-sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}


# 클러스터 분석차트의 CSS
div[data-testid="stVerticalBlockBorderWrapper"] > div { 
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.04), 0 12px 24px rgba(0,0,0,0.08);
    border: 1px solid #F1F3F5;

}
    
.chart-title {
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)

## ============================================================================
# 페이지 제목 설정
## ============================================================================

st.markdown(
    """
    <h2 style="margin-top: -30px; margin-bottom: 10px;">📊 광고 데이터 정보</h2>
    """,
    unsafe_allow_html=True
)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# =============================================================================
# 데이터 로드
# =============================================================================

BUCKET_NAME = "ivekorea-airflow-practice-taeeunk"
FILE_KEY = "ive_ml/Clustering/IVE_CLUSTER_MAPPING_MANUAL.parquet"

# 매핑 데이터 (INDUSTRY/OS_TYPE/LIMIT_TYPE -> CLUSTER)
@st.cache_data(max_entries=1)
def load_mapping_data():
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
        )
        response = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        df = pd.read_parquet(
            BytesIO(response['Body'].read()), 
            engine='pyarrow'
        )
        return df
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

mapping_df = load_mapping_data()

# =============================================================================
# session_state 및 기본값 설정
# =============================================================================

industry = st.session_state.get('selected_industry', "금융/보험")
os_input = st.session_state.get('selected_os', "WEB")
limited = st.session_state.get('selected_limited', "UNLIMITED")
highlight = st.session_state.get('selected_highlight', "이익")

mapping_df['INDUSTRY'] = mapping_df['INDUSTRY'].astype(str).str.strip()
mapping_df['OS_TYPE'] = mapping_df['OS_TYPE'].astype(str).str.strip().str.lower()
mapping_df['LIMIT_TYPE'] = mapping_df['LIMIT_TYPE'].astype(str).str.strip()

industry_clean = industry.strip()
os_input_clean = os_input.strip().lower()
limited_clean = limited.strip()

# 사용자 선택사항 필터링
result_row = mapping_df[
        (mapping_df['INDUSTRY'] == industry_clean) &
        (mapping_df['OS_TYPE'] == os_input_clean) &
        (mapping_df['LIMIT_TYPE'] == limited_clean)
    ]

# 클러스터 추출
if not result_row.empty:
    cluster_num = int(result_row['GMM_CLUSTER'].values[0]) 
    st.session_state['cluster_num'] = cluster_num
else:
    # 3등분 컬럼으로 가운데 정렬
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="color: gray; text-align: center; margin-top: 10px;">
                찾으시는 조합의 데이터가 부족합니다.<br>
                다른 조건을 선택해 주세요.
            </div>
        """, unsafe_allow_html=True)
    st.stop()
cluster_num = int(cluster_num)

## ============================================================================
# 데이터 로드
## ============================================================================

@st.cache_data(max_entries=1)
def load_df(cluster_n):
    target_columns = [
        'INDUSTRY', 'OS_TYPE', 'LIMIT_TYPE',
        '1000_W_EFFICIENCY', 'CVR', 'ATS', 
        'SHAPE', 'MDA', 'START_TIME', 'TIME_TURN',
        'GMM_CLUSTER'
    ]
    file_key = f"ive_ml/Clustering/IVE_ANALYTICS_CLUSTER_{cluster_n}.parquet"

    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
        )
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        df = pd.read_parquet(
            BytesIO(response['Body'].read()), 
            columns=target_columns,
            engine='pyarrow'
        )
        return df
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None  

filtered_df = load_df(cluster_num)

# =============================================================================
# KPI
# =============================================================================

# 기초 프레임 구축
col1, col2, col3 = st.columns(3)

if not filtered_df.empty:
    eff_value = filtered_df['1000_W_EFFICIENCY'].mean()
    cvr_value = filtered_df['CVR'].mean()*100
    display_eff = f"{int(eff_value):,}"
    display_cvr = f"{cvr_value:.2f}%"
    time_turn_value = filtered_df['TIME_TURN'].mean()
else:
    display_eff = "-"
    display_cvr = "-"
    time_turn_value = "-"

col1, col2, col3 = st.columns(3, gap="small")

# KPI 설정
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TURN</div>
        <div class="kpi-value">{time_turn_value:.2f}</div>
        <div class="kpi-sub">전환 수 평균</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">CVR</div>
        <div class="kpi-value">{display_cvr}</div>
        <div class="kpi-sub">전환율 평균</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">1000_W_EFFICIENCY</div>
        <div class="kpi-value">{display_eff}</div>
        <div class="kpi-sub">전환당 평균(천 원)</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# =============================================================================
# 클러스터 분포 차트
# =============================================================================
with st.container():
    st.markdown('<div class="full-width-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📊 클러스터 분석 차트</div>', unsafe_allow_html=True)

    if 'cluster_num' in st.session_state and mapping_df is not None:
        c_num = st.session_state['cluster_num']
        
        target_df = mapping_df[mapping_df['GMM_CLUSTER'] == c_num].copy()

        if not target_df.empty:
            # (1) 산업군
            df_ind = target_df['INDUSTRY'].value_counts().reset_index()
            df_ind.columns = ['Label', 'Count']
            df_ind['Category'] = '산업군'

            # (2) OS
            df_os = target_df['OS_TYPE'].value_counts().reset_index()
            df_os.columns = ['Label', 'Count']
            df_os['Category'] = 'OS'

            # (3) 목표 제한 여부
            df_qt = target_df['LIMIT_TYPE'].value_counts().reset_index()
            df_qt.columns = ['Label', 'Count']
            df_qt['Category'] = '목표 제한 여부'

            # (4) 데이터 합치기
            final_chart_df = pd.concat([df_ind, df_os, df_qt])

            # (5) 차트 생성
            chart = alt.Chart(final_chart_df).mark_bar(
                cornerRadiusTopLeft=5, 
                cornerRadiusTopRight=5
            ).encode(
                x=alt.X('Label', sort=None, title=None, axis=alt.Axis(labelAngle=0)), 
                y=alt.Y('Count', title='빈도수'),
                color=alt.Color('Category', title='구분', 
                                scale=alt.Scale(range=['#FF6C6C', '#4CA8FF', '#56D97D'])),
                tooltip=['Category', 'Label', 'Count']
            ).properties(
                height=300,
                width='container' 
            ).configure_axis(
                grid=False,
                labelFontSize=12
            ).configure_view(
                strokeWidth=0
            )
            
            st.altair_chart(chart, use_container_width=True)
        
        else:
            st.info("차트를 표시할 데이터가 없습니다.")
            
    else:
        st.warning("클러스터 정보나 매핑 데이터를 불러올 수 없습니다.")

    st.markdown('</div>', unsafe_allow_html=True)



st.text("") # 여백
st.text("") # 여백
st.text("") # 여백


# =============================================================================
# 기술 통계
# =============================================================================
st.subheader("기술 통계")

tab1, tab2 = st.tabs(["요약 통계", "상관관계"])

with tab1:
    st.write("**필터링된 데이터의 기술 통계량**")
    stats_df = filtered_df.describe()
    st.dataframe(stats_df, width='stretch')

with tab2:
    st.write("**변수 간 상관관계**")
    numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
    corr_matrix = filtered_df[numeric_cols].corr()
    st.dataframe(
        corr_matrix.style.background_gradient(cmap='RdYlBu', vmin=-1, vmax=1),
        width='stretch'
    )