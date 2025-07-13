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

# ----------------------------------------
# ✅ 1. 시군구별 전력 사용량 총합 비교
# ----------------------------------------
st.header("🔍 시군구별 전력 사용량 비교")

col1, col2 = st.columns(2)
with col1:
    selected_region = st.selectbox("시도 선택", sorted(df["시도"].unique()))
with col2:
    selected_contract = st.selectbox("계약종별 선택", sorted(df["계약종별"].unique()))

# 필터링된 데이터
filtered_df = df[
    (df["시도"] == selected_region) &
    (df["계약종별"] == selected_contract)
].copy()

filtered_df["총합"] = filtered_df[month_columns].sum(axis=1)
df_compare = filtered_df[["시군구", "총합"]].sort_values(by="총합", ascending=False)

st.subheader(f"📊 {selected_region} - {selected_contract} 전력 사용량 총합 (시군구별)")
fig_bar = px.bar(
    df_compare,
    x="시군구",
    y="총합",
    labels={"총합": "전력사용량(kWh)", "시군구": "지역"},
    text="총합"
)
fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_bar)
# ----------------------------------------
# ✅ 2. 계약종별 월별 전력 사용량 비교 (시군구 선택 + 자동 그래프)
# ----------------------------------------
st.header(f"📈 {selected_region} 시군구별 계약종 월별 사용량 비교")

# 선택한 시도의 시군구 목록 필터
sgg_options = sorted(df[df["시도"] == selected_region]["시군구"].unique())
selected_sgg = st.selectbox("시군구 선택", sgg_options)

# "합계" 제외한 계약종 목록 자동 필터
all_contracts = df[
    (df["시도"] == selected_region) &
    (df["시군구"] == selected_sgg)
]["계약종별"].unique().tolist()
filtered_contracts = sorted([c for c in all_contracts if "합계" not in c])

# 해당 시군구 + 계약종별 데이터
compare_df = df[
    (df["시도"] == selected_region) &
    (df["시군구"] == selected_sgg) &
    (df["계약종별"].isin(filtered_contracts))
]

# 월별 합계 정리
grouped = compare_df.groupby("계약종별")[month_columns].sum().T
grouped.index.name = "월"
grouped.reset_index(inplace=True)
grouped["월"] = pd.Categorical(grouped["월"], categories=month_columns, ordered=True)

# 시각화용 long-form
melted = grouped.melt(id_vars="월", var_name="계약종별", value_name="전력사용량")

# 꺾은선 그래프
fig_line = px.line(
    melted,
    x="월",
    y="전력사용량",
    color="계약종별",
    markers=True,
    title=f"{selected_region} {selected_sgg} 계약종별 월별 전력 사용량"
)
st.plotly_chart(fig_line)

# ▶ 자동 하이라이트
peak_row = melted.loc[melted["전력사용량"].idxmax()]
st.success(
    f"✅ **최고 사용량**: **{peak_row['계약종별']}** 계약종이 **{peak_row['월']}**에 **{int(peak_row['전력사용량']):,} kWh** 사용"
)

    st.success(
        f"✅ **가장 많은 전력 사용**: **{peak_contract}** 계약종이 **{peak_month}**에 **{int(peak_value):,} kWh** 사용"
    )
else:
    st.info("계약종을 하나 이상 선택해주세요.")
