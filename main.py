import streamlit as st
import pandas as pd
import plotly.express as px

# ✅ 데이터 불러오기
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("energy(2024).csv", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("energy(2024).csv", encoding='cp949')

    df.columns = df.columns.str.strip()
    df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)

    # 월별 숫자 컬럼 정리
    month_columns = [col for col in df.columns if any(str(m) + "월" in col for m in range(1, 13))]
    for month in month_columns:
        df[month] = pd.to_numeric(df[month].astype(str).str.replace(",", "").str.strip(), errors='coerce')

    return df, month_columns

df, month_columns = load_data()

# ✅ 연도 선택
st.title("시도별 연간 전력 사용량 비교")
years = df["연도"].unique()
selected_year = st.selectbox("연도를 선택하세요", sorted(years))

# ✅ 시도별 연간 전력 사용량 계산
df_year = df[df["연도"] == selected_year]
df_grouped = df_year.groupby("시도")[month_columns].sum()
df_grouped["연간총합"] = df_grouped.sum(axis=1)
df_sorted = df_grouped.sort_values("연간총합", ascending=False).reset_index()

# ✅ 막대 그래프
st.subheader("시도별 연간 전력 사용량 (막대 그래프)")
bar_fig = px.bar(
    df_sorted,
    x='시도',
    y='연간총합',
    text='연간총합',
    labels={'연간총합': '연간 전력 사용량 (kWh)', '시도': '지역'},
    title=f"{selected_year}년 시도별 연간 전력 사용량"
)
bar_fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
bar_fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(bar_fig)

# ✅ 지도용 시도-영문 매핑
sido_name_map = {
    '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu', '인천광역시': 'Incheon',
    '광주광역시': 'Gwangju', '대전광역시': 'Daejeon', '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
    '경기도': 'Gyeonggi-do', '강원도': 'Gangwon-do', '충청북도': 'Chungcheongbuk-do',
    '충청남도': 'Chungcheongnam-do', '전라북도': 'Jeollabuk-do', '전라남도': 'Jeollanam-do',
    '경상북도': 'Gyeongsangbuk-do', '경상남도': 'Gyeongsangnam-do', '제주특별자치도': 'Jeju-do'
}

df_sorted["region_eng"] = df_sorted["시도"].map(sido_name_map)

# ✅ 지도 시각화 (대한민국 Choropleth)
st.subheader("시도별 연간 전력 사용량 (지도)")
fig_map = px.choropleth(
    df_sorted,
    geojson="https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea-provinces.json",
    featureidkey="properties.name_eng",
    locations="region_eng",
    color="연간총합",
    color_continuous_scale="YlOrRd",
    hover_name="시도",
    hover_data={"연간총합": ":,.0f"},
    title="대한민국 시도별 연간 전력 사용량"
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
st.plotly_chart(fig_map)
