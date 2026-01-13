# =============================================================================
# 광고 추천 모델 페이지
# =============================================================================

import streamlit as st
import pandas as pd
import pickle
from sklearn.preprocessing import MinMaxScaler
import altair as alt
from io import BytesIO
import boto3

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
    font-size: 32px;
    color: #E85A4F;
    margin-left: 20px;
    font-weight: 650;
    margin-bottom: 15px;
}

.kpi-sub_title {
    font-size: 17px;
    color: #111827;
    margin-left: 20px;
}
        
.kpi-sub_title1 {
    font-size: 17px;
    color: #111827;
    margin-right: 15px;    
    margin-left: 20px;
}
    
.kpi-value {
    font-size: 18px;
    font-weight: 650;
    color: #E85A4F;
}

.kpi-sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}

</style>
""", unsafe_allow_html=True)

## ============================================================================
# 페이지 제목 설정
## ============================================================================

st.markdown(
    """
    <h2 style="margin-top: -30px;">🔍 광고 추천 모델</h2>
    """,
    unsafe_allow_html=True
)
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# =============================================================================
# 매핑 데이터 로드
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
        
        # 전체를 읽지 않고 지정한 columns만 로드
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

highlight = st.session_state['selected_highlight']

mapping_df['INDUSTRY'] = mapping_df['INDUSTRY'].astype(str).str.strip()
mapping_df['OS_TYPE'] = mapping_df['OS_TYPE'].astype(str).str.strip().str.lower()
mapping_df['LIMIT_TYPE'] = mapping_df['LIMIT_TYPE'].astype(str).str.strip()

industry_clean = industry.strip()
os_input_clean = os_input.strip().lower()
limited_clean = limited.strip()

# =============================================================================
# 데이터 필터링
# =============================================================================

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
# 데이터 및 모델 로드
## ============================================================================

# 데이터 로드
@st.cache_data(max_entries=1)
def load_df(cluster_n):
    target_columns = [
        'INDUSTRY', 'OS_TYPE', 'LIMIT_TYPE',
        '1000_W_EFFICIENCY', 'CVR', 'ABS', 
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

# 모델 로드
@st.cache_resource(max_entries=1)
def load_model(cluster_n):
    file_key = f"ive_ml/Models/Cluster_{cluster_n}_cat_re_models.pkl"

    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            region_name=st.secrets.get("AWS_DEFAULT_REGION", "ap-southeast-2")
        )

        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        model_content = response['Body'].read()

        model = pickle.loads(model_content)
        return model

    except Exception as e:
        st.error(f"S3에서 클러스터 {cluster_n} 모델을 불러오는 중 오류 발생: {e}")
        return None
    
df = load_df(cluster_num)
model = load_model(cluster_num)

# =============================================================================
# 예측 함수 및 TOP 리스트
# =============================================================================
# # x : SHAPE, MDA, START_TIME -> CVR, 1000_W_EFFICIENCY, ABS 예측
@st.cache_resource
def prediction_TOP_3(df, _model, highlight):
    unique_conditions = df[['SHAPE', 'MDA', 'START_TIME']].drop_duplicates()
    result_df = unique_conditions.copy()
    result_df['MDA'] = result_df['MDA'].astype(str)
    
    targets = {
            'CVR': 'Pred_CVR',
            '1000_W_EFFICIENCY': 'Pred_EFF',
            'ABS': 'Pred_ABS'
        }

    for model_key_name, col_name in targets.items():
        target_model = _model[model_key_name]
            
        if hasattr(target_model, 'predict'):
            result_df[col_name] = target_model.predict(unique_conditions)
        else:
            result_df[col_name] = float(target_model)
    
    count_df = df.groupby(['SHAPE', 'MDA', 'START_TIME']).size().reset_index(name='Data_Count')
    count_df['MDA'] = count_df['MDA'].astype(str)
    result_df = pd.merge(result_df, count_df, on=['SHAPE', 'MDA', 'START_TIME'], how='left')
    result_df['Data_Count'] = result_df['Data_Count'].fillna(0)
    result_df = result_df[result_df['Data_Count'] >= 10].copy()

    scaler = MinMaxScaler(feature_range=(0, 100))
    scaled_vals = scaler.fit_transform(result_df[['Pred_CVR', 'Pred_EFF', 'Pred_ABS']])
    result_df['CVR_scaled'] = scaled_vals[:, 0]
    result_df['EFF_scaled'] = scaled_vals[:, 1]
    result_df['ABS_scaled'] = scaled_vals[:, 2]

    # 중점 사항에 따른 가중치 수정
    if highlight == "이익":
        result_df['score'] = result_df['CVR_scaled']*0.5 + result_df['EFF_scaled']*0.25 + result_df['ABS_scaled']*0.25
    elif highlight == "비용":
        result_df['score'] = result_df['CVR_scaled']*0.25 + result_df['EFF_scaled']*0.5 + result_df['ABS_scaled']*0.25
    elif highlight == "안정성":
        result_df['score'] = result_df['CVR_scaled']*0.25 + result_df['EFF_scaled']*0.25 + result_df['ABS_scaled']*0.5

    top_10 = result_df.sort_values('score', ascending=False).head(10).copy()
    top = result_df.sort_values('score', ascending=False).head(3).copy()

    top['rank_label'] = [1,2,3]
    top1 = top[top['rank_label']==1].reset_index(drop=True)
    top2 = top[top['rank_label']==2].reset_index(drop=True)
    top3 = top[top['rank_label']==3].reset_index(drop=True)
    
    return top1, top2, top3, top, top_10

top1, top2, top3, top, top_10 = prediction_TOP_3(df, model, highlight)

 
# =============================================================================
# TOP_3 출력
# =============================================================================
col1, col2, col3 = st.columns(3)

# TOP_1
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TOP 1<span style='color:gray; font-size:18px; margin-left: 6px;'> [효율 점수 : {top1['score'].values[0]:.2f}] </span> </div>
        <div>
                <span class="kpi-sub_title1">수행 방식</span>
                <span class="kpi-value">
                <span style="color:black; font-weight:350;">:</span> {top1['SHAPE'].values[0]}</span>
        <div>
                <span class="kpi-sub_title">매체 플랫폼 :</span>
                <span class="kpi-value">{top1['MDA'].values[0]}</span>
            </div>
        <div>
                <span class="kpi-sub_title">시작 시간대 :</span>
                <span class="kpi-value">{top1['START_TIME'].values[0]}</span>
            </div>
        <div class="kpi-sub">&nbsp;</div>
    </div>
    """, unsafe_allow_html=True
    )

# TOP_2
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TOP 2<span style='color:gray; font-size:18px; margin-left: 6px;'> [효율 점수 : {top2['score'].values[0]:.2f}] </span> </div>
        <div>
                <span class="kpi-sub_title1">수행 방식</span>
                <span class="kpi-value">
                <span style="color:black; font-weight:350;">:</span> {top2['SHAPE'].values[0]}</span>
        <div>
                <span class="kpi-sub_title">매체 플랫폼 :</span>
                <span class="kpi-value">{top2['MDA'].values[0]}</span>
            </div>
        <div>
                <span class="kpi-sub_title">시작 시간대 :</span>
                <span class="kpi-value">{top2['START_TIME'].values[0]}</span>
            </div>
        <div class="kpi-sub">&nbsp;</div>
    </div>
    """, unsafe_allow_html=True
    )

# TOP_3
with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">TOP 3<span style='color:gray; font-size:18px; margin-left: 6px;'> [효율 점수 : {top3['score'].values[0]:.2f}] </span> </div>
        <div>
                <span class="kpi-sub_title1">수행 방식</span>
                <span class="kpi-value">
                <span style="color:black; font-weight:350;">:</span> {top3['SHAPE'].values[0]}</span>
        <div>
                <span class="kpi-sub_title">매체 플랫폼 :</span>
                <span class="kpi-value">{top3['MDA'].values[0]}</span>
            </div>
        <div>
                <span class="kpi-sub_title">시작 시간대 :</span>
                <span class="kpi-value">{top3['START_TIME'].values[0]}</span>
            </div>
        <div class="kpi-sub">&nbsp;</div>
    </div>
    """, unsafe_allow_html=True
    )

st.divider()

# =============================================================================
# 예산안 편성 추천
# =============================================================================

st.subheader("광고 예산안 배분")

# 도넛 차트
top_chart = top.copy()
rank_order = ['TOP 1', 'TOP 2', 'TOP 3']
color_range = ['#FF6C6C', '#4CA8FF', '#56D97D']

# 수식 계산(예산 분배 방법) - 100% SPLIT
total_score = top_chart['score'].sum()
top_chart['rate_val'] = (top_chart['score'] / total_score) * 100 
top_chart['rate_val'] = top_chart['rate_val'].round(1)
top_chart['rate_str'] = top_chart['rate_val'].astype(str) + "%"
top_chart['rank_label'] = [f'TOP {i+1}' for i in range(len(top_chart))]

# 차트 및 범례 생성
base = alt.Chart(top_chart).encode(
    theta=alt.Theta("rate_val", stack=True) 
)

pie = base.mark_arc(outerRadius=110, innerRadius=65).encode(
    color=alt.Color("rank_label", 
                    scale=alt.Scale(domain=rank_order, range=color_range),
                    sort=rank_order,
                    legend=alt.Legend(
                        orient='none',       
                        legendX=48,           
                        legendY=20,          
                        direction='vertical', 
                        title=None,             
                        labelFontSize=16,       
                        symbolType='circle'     
                    )),
    order=alt.Order("rank_label", sort="ascending"), 
    tooltip=["rank_label", "rate_str"] 
)

# 도넛 위에 라벨
text = base.mark_text(radius=155, fontSize=24).encode(
    text=alt.Text("rate_str"),
    order=alt.Order("rank_label", sort="ascending"),
    color=alt.value("black")  
)

chart = (pie + text).properties(
    height=350
)

st.altair_chart(chart, use_container_width=True)

st.divider()

# =============================================================================
# TOP_10 리스트 정리
# =============================================================================
st.subheader("TOP 10")
tab1, tab2 = st.tabs(["광고 형태 추천","추가 설명"])

# TOP_15 표
with tab1:
    stats_df = top_10
    st.dataframe(stats_df, width='stretch', height='stretch')

# 추가 설명
with tab2:
    st.write("🔍 계산 과정")
    st.markdown("""
    <div><p> 광고 효율 점수(Efficiency)를 기준으로 상위 광고 캠페인 추천</p>
            <p style= 'color:gray; margin:2px 0;'>* 광고 효율 점수: CVR + (1-CPA)</p>
            <p style= 'color:gray; margin:2px 0;'>* CVR은 성능지표라 높을수록 효과적</p>
            <p style= 'color:gray; margin:2px 0;'>* 1000_W_EFFICIENCY는 천원당 전환 수라 높을수록 효율적</p>
            <p style= 'color:gray; margin:2px 0;'>* ABS는 목표 전환 수 대비 실제 전환 수라 높을수록 효율적</p>
            <p style= 'color:gray; margin:2px 0;'>→  <b>즉, 광고 효율 점수가 높을수록</b> 👍🏻</p>
    </div>          
    """, unsafe_allow_html=True)