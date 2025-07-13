import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------
# 📦 데이터 로드 및 전처리
# --------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("energy(2024).csv", encoding='utf-8')
    df.columns = df.columns.str.strip()
    df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)

    # 월별 컬럼
    month_columns = [col for col in df.columns if "월" in col and col.strip()[:2].isdigit()]
    for col in month_columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors='coerce')

    df = df[df["계약종별"] != "합계"].copy()
    df["연간총합"] = df[month_columns].sum(axis=1)

    # 시도 영어 매핑
    sido_name_map = {
        '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu', '인천광역시': 'Incheon',
        '광주광역시': 'Gwangju', '대전광역시': 'Daejeon', '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
        '경기도': 'Gyeonggi-do', '강원도': 'Gangwon-do', '충청북도': 'Chungcheongbuk-do',
        '충청남도': 'Chungcheongnam-do', '전라북도': 'Jeollabuk-do', '전라남도': 'Jeollanam-do',
        '경상북도': 'Gyeongsangbuk-do', '경상남도': 'Gyeongsangnam-do', '제주특별자치도': 'Jeju-do'
    }
    df["region_eng"] = df["시도"].map(sido_name_map)

    return df, month_columns

df, month_columns = load_data()
contract_list = sorted(df["계약종별"].unique())

# --------------------------
# 🗺️ 1. 계약종별 시도 전력 사용량 지도
# --------------------------
st.title("전력 사용량 시각화 · 탐색 플랫폼")

st.header("🗺️ 계약종별 시도 전력 사용량 지도")
selected_contract = st.selectbox("계약종을 선택하세요", contract_list)

df_grouped = df.groupby(["시도", "계약종별", "region_eng"])["연간총합"].sum().reset_index()
df_map = df_grouped[df_grouped["계약종별"] == selected_contract]

fig_map = px.choropleth(
    df_map,
    geojson="https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea-provinces.json",
    locations="region_eng",
    featureidkey="properties.name_eng",
    color="연간총합",
    hover_name="시도",
    hover_data={"연간총합": ":,.0f"},
    color_continuous_scale="YlOrRd",
    title=f"{selected_contract} 계약종 기준 시도별 연간 전력 사용량"
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
st.plotly_chart(fig_map)

# --------------------------
# 📊 2. 시군구별 계약종 꺾은선 그래프
# --------------------------
st.header("📊 시군구별 계약종 월별 사용량 비교")

selected_sido = st.selectbox("시도 선택", sorted(df["시도"].unique()))
sgg_list = df[df["시도"] == selected_sido]["시군구"].unique().tolist()
selected_sgg = st.selectbox("시군구 선택", sorted(sgg_list))

df_filtered = df[
    (df["시도"] == selected_sido) & (df["시군구"] == selected_sgg)
]
df_filtered = df_filtered[df_filtered["계약종별"] != "합계"]

grouped = df_filtered.groupby("계약종별")[month_columns].sum().T
grouped.index.name = "월"
grouped.reset_index(inplace=True)
grouped["월"] = pd.Categorical(grouped["월"], categories=month_columns, ordered=True)
melted = grouped.melt(id_vars="월", var_name="계약종별", value_name="전력사용량")

fig_line = px.line(
    melted,
    x="월",
    y="전력사용량",
    color="계약종별",
    markers=True,
    title=f"{selected_sido} {selected_sgg} 계약종별 월별 전력 사용량"
)
st.plotly_chart(fig_line)

# 최고/최저 사용량 하이라이트
peak = melted.loc[melted["전력사용량"].idxmax()]
low = melted.loc[melted["전력사용량"].idxmin()]

st.success(f"✅ 최고 사용: **{peak['계약종별']}** - **{peak['월']}**에 **{int(peak['전력사용량']):,} kWh**")
st.info(f"🔻 최저 사용: **{low['계약종별']}** - **{low['월']}**에 **{int(low['전력사용량']):,} kWh**")

# --------------------------
# 🔎 3. 탐색 도우미: 급등한 달 찾기
# --------------------------
st.header("🔎 탐색 도우미: 급등한 달 찾기")

selected_analysis_contract = st.selectbox("계약종 선택 (급등 탐색)", contract_list, index=contract_list.index("주택용"))

delta_df = df[df["계약종별"] == selected_analysis_contract].copy()
delta_df["시도_시군구"] = delta_df["시도"] + " " + delta_df["시군구"]

# 월별 변화량 계산
delta_cols = []
for i in range(1, 12):
    m1 = f"{i}월"
    m2 = f"{i+1}월"
    col = f"{m1}-{m2} 증감"
    delta_df[col] = delta_df[m2] - delta_df[m1]
    delta_cols.append(col)

# 최대 증가량 행 찾기
delta_df["최대증가량"] = delta_df[delta_cols].max(axis=1)
delta_df["증가월"] = delta_df[delta_cols].idxmax(axis=1)
top_row = delta_df.loc[delta_df["최대증가량"].idxmax()]

# 결과 출력
st.warning(
    f"📈 **가장 큰 전력 급등**: {top_row['시도']} {top_row['시군구']} / 계약종: {selected_analysis_contract} / "
    f"{top_row['증가월']}에 **{int(top_row['최대증가량']):,} kWh** 증가"
)

# 상위 5개 지역 표
st.markdown("#### ⚡ 급등 상위 5개 지역")
st.dataframe(
    delta_df.sort_values("최대증가량", ascending=False)[
        ["시도", "시군구", "증가월", "최대증가량"]
    ].head(5).rename(columns={"최대증가량": "증가량(kWh)"})
)
