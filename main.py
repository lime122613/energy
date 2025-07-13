import streamlit as st
import pandas as pd
import plotly.express as px

# 데이터 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("energy(2024).csv", encoding='utf-8')
    except:
        df = pd.read_csv("energy(2024).csv", encoding='cp949')

    df.columns = df.columns.str.strip()
    df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)

    month_columns = [col for col in df.columns if any(str(m) + "월" in col for m in range(1, 13))]
    for col in month_columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors='coerce')

    return df, month_columns

df, month_columns = load_data()

st.title("대한민국 전력 사용량 시각화 및 비교 시스템")

# -------------------------------
# ✅ 1. 전국 시도별 전력 사용 지도
# -------------------------------
st.header("📍 대한민국 월별 전력 사용 지도")

selected_month = st.selectbox("비교할 월을 선택하세요", month_columns)

# 시도별 월별 합계 계산
df_sido_month = df.groupby("시도")[selected_month].sum().reset_index()
df_sido_month.columns = ["시도", "전력사용량"]

# 시도 → 영문 매핑
sido_name_map = {
    '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu', '인천광역시': 'Incheon',
    '광주광역시': 'Gwangju', '대전광역시': 'Daejeon', '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
    '경기도': 'Gyeonggi-do', '강원도': 'Gangwon-do', '충청북도': 'Chungcheongbuk-do',
    '충청남도': 'Chungcheongnam-do', '전라북도': 'Jeollabuk-do', '전라남도': 'Jeollanam-do',
    '경상북도': 'Gyeongsangbuk-do', '경상남도': 'Gyeongsangnam-do', '제주특별자치도': 'Jeju-do'
}
df_sido_month["region_eng"] = df_sido_month["시도"].map(sido_name_map)

fig_map = px.choropleth(
    df_sido_month,
    geojson="https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea-provinces.json",
    locations="region_eng",
    featureidkey="properties.name_eng",
    color="전력사용량",
    hover_name="시도",
    hover_data={"전력사용량": ":,.0f"},
    color_continuous_scale="YlOrRd",
    title=f"{selected_month} 시도별 전력 사용량 지도"
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
st.plotly_chart(fig_map)

# -------------------------------
# ✅ 2. 학생용 탐색: 지역+계약종+월별 비교
# -------------------------------
st.header("🔍 전력 사용량 비교 탐색")

col1, col2, col3 = st.columns(3)
with col1:
    selected_region = st.selectbox("시도 선택", sorted(df["시도"].unique()))
with col2:
    selected_contract = st.selectbox("계약종별 선택", sorted(df["계약종별"].unique()))
with col3:
    selected_month2 = st.selectbox("월 선택", month_columns)

# 필터링된 데이터
filtered_df = df[
    (df["시도"] == selected_region) &
    (df["계약종별"] == selected_contract)
]

# 시군구별 전력 사용량
df_compare = filtered_df[["시군구", selected_month2]].sort_values(by=selected_month2, ascending=False)

st.subheader(f"📊 {selected_region} - {selected_contract} - {selected_month2} 시군구별 전력 사용량")
fig_bar = px.bar(
    df_compare,
    x="시군구",
    y=selected_month2,
    labels={selected_month2: "전력사용량(kWh)", "시군구": "지역"},
    text=selected_month2
)
fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_bar)

# -------------------------------
# ✅ 3. 추가 꺾은선 비교 그래프 (선택적)
# -------------------------------
st.subheader(f"📈 {selected_region} - 계약종별 월별 사용량 비교")

selected_contracts = st.multiselect(
    "비교할 계약종을 선택하세요",
    options=sorted(df[df["시도"] == selected_region]["계약종별"].unique()),
    default=[selected_contract]
)

if selected_contracts:
    compare_df = df[
        (df["시도"] == selected_region) &
        (df["계약종별"].isin(selected_contracts))
    ]
    grouped = compare_df.groupby("계약종별")[month_columns].sum().T
    grouped.index.name = "월"
    grouped.reset_index(inplace=True)

    grouped["월"] = pd.Categorical(grouped["월"], categories=month_columns, ordered=True)
    melted = grouped.melt(id_vars="월", var_name="계약종별", value_name="전력사용량")

    fig_line = px.line(
        melted,
        x="월",
        y="전력사용량",
        color="계약종별",
        markers=True
    )
    st.plotly_chart(fig_line)
else:
    st.info("계약종을 선택하세요.")
