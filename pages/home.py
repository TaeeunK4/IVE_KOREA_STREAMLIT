# =============================================================================
# 광고 데이터 정보 페이지
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import altair as alt
import boto3
from io import BytesIO
from PIL import Image
import base64

# =============================================================================
# 1. CSS 설정
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
# 2. 제목 설정
## ============================================================================
st.markdown(
    """
    <h2 style="margin-top: -30px; margin-bottom: 10px;">📊 광고 데이터 정보</h2>
    """,
    unsafe_allow_html=True
)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


# =============================================================================
# 3. 데이터 로드
# =============================================================================
# 3.1 경로 저장 및 데이터 캐싱
BUCKET_NAME = "ivekorea-airflow-practice-taeeunk"
OBJECT_KEY = "image/error_image.jpg"
FILE_KEY = "ive_ml/Clustering/IVE_ANALYTICS_CLUSTER.parquet"

@st.cache_data
def get_s3_resized_png_b64(BUCKET_NAME, OBJECT_KEY, new_width):
    try:
        # 1. boto3 S3 클라이언트 생성
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            region_name=st.secrets.get("AWS_DEFAULT_REGION", "ap-southeast-2")
        )

        # 2. S3에서 객체(이미지) 가져오기
        response = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        image_content = response['Body'].read()

        # 3. 이미지 열기 및 처리
        img = Image.open(BytesIO(image_content))
        img = img.convert("RGBA") # 투명 배경 지원

        # 4. 이미지 비율 유지하며 리사이징 계산
        w_percent = (new_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        
        # 고품질 리사이징
        resized_img = img.resize((new_width, h_size), Image.Resampling.LANCZOS)
        
        # 5. 메모리 버퍼에 PNG 형식으로 저장
        buffer = BytesIO()
        resized_img.save(buffer, format="PNG")
        
        # 6. Base64로 인코딩해서 문자열로 반환
        return base64.b64encode(buffer.getvalue()).decode()

    except Exception as e:
        raise Exception(f"S3 이미지 처리 실패 (Key: {OBJECT_KEY}): {e}")

@st.cache_data
def load_full_data():
    """S3에서 전체 Parquet 데이터를 한 번만 로드하여 캐싱"""
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
        )
        response = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        # Parquet 파일을 메모리 버퍼로 읽어 pandas로 변환
        return pd.read_parquet(BytesIO(response['Body'].read()))
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

image_1 = get_s3_resized_png_b64(BUCKET_NAME, OBJECT_KEY, 32)
mapping_df = load_full_data()

# 3.2 session_state 및 기본값 설정
industry = st.session_state.get('selected_industry', "금융/보험")
os_input = st.session_state.get('selected_os', "WEB")
limited = st.session_state.get('selected_limited', "UNLIMITED")


# =============================================================================
# 4.데이터 필터링
# =============================================================================
# 4.1 문자열 정리(공백 제거 + 소문자 변환)
mapping_df['INDUSTRY'] = mapping_df['INDUSTRY'].astype(str).str.strip()
mapping_df['OS_TYPE'] = mapping_df['OS_TYPE'].astype(str).str.strip().str.lower()
mapping_df['LIMIT_TYPE'] = mapping_df['LIMIT_TYPE'].astype(str).str.strip()

industry_clean = industry.strip()
os_input_clean = os_input.strip().lower()
limited_clean = limited.strip()

# 4.2 사용자 필터링
result_row = mapping_df[
        (mapping_df['INDUSTRY'] == industry_clean) &
        (mapping_df['OS_TYPE'] == os_input_clean) &
        (mapping_df['LIMIT_TYPE'] == limited_clean)
    ]

# 4.3 클러스터 추출 및 예외 처리
if not result_row.empty:
    cluster_num = int(result_row['GMM_CLUSTER'].values[0]) 
    st.session_state['cluster_num'] = cluster_num
else:
    # 3등분 컬럼으로 가운데 정렬
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(f"data:image/png;base64,{image_1}", width=500)
        # HTML로 가운데 정렬 + 줄바꿈
        st.markdown("""
            <div style="color: gray; text-align: center; margin-top: 10px;">
                찾으시는 조합의 데이터가 부족합니다.<br>
                다른 조건을 선택해 주세요.
            </div>
        """, unsafe_allow_html=True)
    st.stop()
    
cluster_num = int(cluster_num)

# 4.4 클러스터 파일 불러오기
@st.cache_data
def load_df(cluster_n):
    """
    S3에서 특정 클러스터 번호에 해당하는 Parquet 파일을 로드합니다.
    """
    # 1. S3 버킷 및 파일 경로 설정 (이미지 경로 기준)
    bucket_name = "ivekorea-airflow-practice-taeeunk"
    file_key = f"ive_ml/Clustering/IVE_ANALYTICS_CLUSTER_{cluster_n}.parquet"
    s3_url = f"s3://{bucket_name}/{file_key}"

    try:
        # 2. pandas의 read_parquet 기능을 사용하여 S3에서 직접 로드
        # storage_options를 통해 secrets.toml에 저장된 인증 정보를 전달합니다.
        df = pd.read_parquet(
            s3_url,
            storage_options={
                "key": st.secrets["AWS_ACCESS_KEY_ID"],
                "secret": st.secrets["AWS_SECRET_ACCESS_KEY"]
            }
        )
        return df
        
    except Exception as e:
        st.error(f"S3에서 클러스터 {cluster_n} 파일을 불러오는 중 오류 발생: {e}")
        return None

filtered_df = load_df(cluster_num)


# =============================================================================
# 5. KPI
# =============================================================================
# 5.1 기초 프레임 구축
col1, col2, col3 = st.columns(3)

if not filtered_df.empty:
    eff_value = filtered_df['1000_W_EFFICIENCY'].mean()
    cvr_value = filtered_df['CVR'].mean()*100
    display_eff = f"{int(eff_value):,}원"
    display_cvr = f"{cvr_value:.2f}%"
    time_turn_value = filtered_df['TIME_TURN'].mean()
else:
    display_eff = "-"
    display_cvr = "-"
    time_turn_value = "-"

col1, col2, col3 = st.columns(3, gap="small")

# 5.2 지표 설정
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
        <div class="kpi-title">CPA</div>
        <div class="kpi-value">{display_eff}</div>
        <div class="kpi-sub">전환당 평균(천 원)</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# =============================================================================
# 6. 클러스터 분포 차트
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

            # (3) 분기
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
# 7. 기술 통계
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