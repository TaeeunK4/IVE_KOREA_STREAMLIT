# =============================================================================
# 광고 추천 모델 페이지
# =============================================================================

import streamlit as st
import pandas as pd
import pickle
from sklearn.preprocessing import RobustScaler
import altair as alt
from io import BytesIO
import boto3
import base64
from PIL import Image


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
# 2. 제목 설정
## ============================================================================

st.markdown(
    """
    <h2 style="margin-top: -30px;">🔍 광고 추천 모델</h2>
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

# 3.2 session_state 및 기본값 설정
industry = st.session_state.get('selected_industry', "금융/보험")
os_input = st.session_state.get('selected_os', "WEB")
limited = st.session_state.get('selected_limited', "UNLIMITED")

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
    
@st.cache_data(max_entries=1) # 메모리에 데이터프레임을 딱 하나만 유지하여 OOM 방지
def load_full_data():
    """S3에서 필요한 칼럼만 선택적으로 로드하여 메모리 최적화"""
    # 사용자가 정의한 9개 칼럼 + 필터링용 클러스터 칼럼
    target_columns = [
        'INDUSTRY', 'OS_TYPE', 'LIMIT_TYPE', # limit_type 대응
        '1000_W_EFFICIENCY', 'CVR', 'ABS', 
        'SHAPE', 'MDA', 'START_TIME',
        'GMM_CLUSTER' # 클러스터 번호를 뽑기 위해 반드시 필요함
    ]
    
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
            columns=target_columns,
            engine='pyarrow'
        )
        return df
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None  
    
image_1 = get_s3_resized_png_b64(BUCKET_NAME, OBJECT_KEY, 32)    
mapping_df = load_full_data()


# 3.4 매핑 데이터 전처리
mapping_df['INDUSTRY'] = mapping_df['INDUSTRY'].astype(str).str.strip()
mapping_df['OS_TYPE'] = mapping_df['OS_TYPE'].astype(str).str.strip().str.lower()
mapping_df['LIMIT_TYPE'] = mapping_df['LIMIT_TYPE'].astype(str).str.strip()

industry_clean = industry.strip()
os_input_clean = os_input.strip().lower()
limited_clean = limited.strip()


## ============================================================================
# 4. 필터링
## ============================================================================
# 4.1 지정값 필터링
result_row = mapping_df[
        (mapping_df['INDUSTRY'] == industry_clean) &
        (mapping_df['OS_TYPE'] == os_input_clean) &
        (mapping_df['LIMIT_TYPE'] == limited_clean)
    ]

# 4.1 클러스터 조합 찾기 및 session_state 저장
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


## ============================================================================
# 5. 모델 데이터 로드
## ============================================================================
@st.cache_data(max_entries=1)
def load_df(cluster_n):
    file_key = f"ive_ml/Clustering/IVE_ANALYTICS_CLUSTER_{cluster_n}.parquet"
    s3_url = f"s3://{BUCKET_NAME}/{file_key}"

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

@st.cache_resource(max_entries=1)
def load_model(cluster_n):
    file_key = f"ive_ml/Models/Cluster_{cluster_n}_cat_re_models.pkl"

    try:
        # 2. boto3 클라이언트 생성
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            region_name=st.secrets.get("AWS_DEFAULT_REGION", "ap-southeast-2")
        )

        # 3. S3에서 객체 가져오기
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        model_content = response['Body'].read()

        # 4. pickle로 모델 로드
        model = pickle.loads(model_content)
        return model

    except Exception as e:
        st.error(f"S3에서 클러스터 {cluster_n} 모델을 불러오는 중 오류 발생: {e}")
        return None
    

# 5.4 함수 호출 및 저장
df = load_df(cluster_num)
model = load_model(cluster_num)


# =============================================================================
# 6. 예측 함수 및 TOP 리스트
# =============================================================================
@st.cache_resource
def prediction_TOP_3(df, _model):
    unique_conditions = df[['SHAPE', 'MDA', 'START_TIME']].drop_duplicates()
    result_df = unique_conditions.copy()
    result_df['MDA'] = result_df['MDA'].astype(str)

    pred_cvr = _model['CVR'].predict(unique_conditions)
    result_df['Pred_CVR'] = pred_cvr

    pred_eff = _model['1000_W_EFFICIENCY'].predict(unique_conditions)
    result_df['Pred_EFF'] = pred_eff

    pred_abs = _model['ABS'].predict(unique_conditions)
    result_df['Pred_ABS'] = pred_abs

    count_df = df.groupby(['SHAPE', 'MDA', 'START_TIME']).size().reset_index(name='Data_Count')
    count_df['MDA'] = count_df['MDA'].astype(str)
    result_df = pd.merge(
        result_df,
        count_df,
        on=['SHAPE', 'MDA', 'START_TIME'],
        how='left'
    )

    result_df['Data_Count'] = result_df['Data_Count'].fillna(0)
    result_df = result_df[result_df['Data_Count'] >= 10].copy()

    scaler = RobustScaler()
    scaled_vals = scaler.fit_transform(result_df[['Pred_CVR', 'Pred_EFF', 'Pred_ABS']])
    result_df['CVR_scaled'] = scaled_vals[:, 0]
    result_df['EFF_scaled'] = scaled_vals[:, 1]
    result_df['ABS_scaled'] = scaled_vals[:, 1]

    result_df['score'] = result_df['CVR_scaled'] + result_df['EFF_scaled'] + result_df['ABS_scaled']

    top_10 = result_df.sort_values('score', ascending=False).head(10).copy()
    top = result_df.sort_values('score', ascending=False).head(3).copy()

    top['rank_label'] = [1,2,3]
    top1 = top[top['rank_label']==1].reset_index(drop=True)
    top2 = top[top['rank_label']==2].reset_index(drop=True)
    top3 = top[top['rank_label']==3].reset_index(drop=True)
    
    return top1, top2, top3, top, top_10

top1, top2, top3, top, top_10 = prediction_TOP_3(df, model)

 
# =============================================================================
# 7. TOP_3 출력
# =============================================================================
col1, col2, col3 = st.columns(3)

# 7.1 TOP_1
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

# 7.2 TOP_2
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

# 7.3 TOP_3
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
# 8. 예산안
# =============================================================================
st.subheader("광고 예산안 배분")


# 8.1 도넛 차트
top_chart = top.copy()
rank_order = ['TOP 1', 'TOP 2', 'TOP 3']
color_range = ['#FF6C6C', '#4CA8FF', '#56D97D']

# 8.2 수식 계산(예산 분배 방법)
total_score = top_chart['score'].sum()
top_chart['rate_val'] = (top_chart['score'] / total_score) * 100 
top_chart['rate_val'] = top_chart['rate_val'].round(1)
top_chart['rate_str'] = top_chart['rate_val'].astype(str) + "%"
top_chart['rank_label'] = [f'TOP {i+1}' for i in range(len(top_chart))]

# 8.3 차트 및 범례 생성
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

# 8.4 도넛 위에 라벨
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
# 9. TOP_10
# =============================================================================
st.subheader("TOP 10")
tab1, tab2 = st.tabs(["광고 형태 추천","추가 설명"])

# 9.1 TOP_15 표
with tab1:
    stats_df = top_10
    st.dataframe(stats_df, width='stretch', height='stretch')

# 9.2 추가 설명
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