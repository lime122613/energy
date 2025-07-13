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
    month_columns = [f"{i}월" for i in range(1, 13)]
    for col in month_columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors='coerce')

    df = df[df["계약종별"] != "합계"].copy()
    df["연간총합"] = df[month_columns].sum(axis=1)

    return df, month_columns

df, month_columns = load_data()
contract_list = sorted(df["계약종별"].unique())

# --------------------------
# 📊 1. 계약종별 시도 전력 사용량 막대그래프
# --------------------------
st.title("전력 사용량 시각화 · 탐색 플랫폼")

st.header("📊 계약종별 시도 전력 사용량 비교")

selected_contract = st.selectbox("계약종을 선택하세요", contract_list)

df_grouped = df.groupby(["시도", "계약종별"])["연간총합"].sum().reset_index()
df_selected = df_grouped[df_grouped["계약종별"] == selected_contract].sort_values(by="연간총합", ascending=False)

fig_bar = px.bar(
    df_selected,
    x="시도",
    y="연간총합",
    text="연간총합",
    labels={"연간총합": "전력 사용량 (kWh)", "시도": "지역"},
    title=f"{selected_contract} 계약종 기준 시도별 연간 전력 사용량 (내림차순)",
)
fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_bar.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_bar)

# --------------------------
# 📈 2. 시군구별 계약종 월별 사용량 꺾은선 그래프
# --------------------------
st.header("📈 시군구별 계약종 월별 사용량 비교")

selected_sido = st.selectbox("시도 선택", sorted(df["시도"].unique()))
sgg_list = df[df["시도"] == selected_sido]["시군구"].unique().tolist()
selected_sgg = st.selectbox("시군구 선택", sorted(sgg_list))

df_filtered = df[
    (df["시도"] == selected_sido) & (df["시군구"] == selected_sgg)
]
df_filtered = df_filtered[df_filtered["계약종별"] != "합계"]

# 월 정렬 오류 방지용 정렬
month_order = [f"{i}월" for i in range(1, 13)]

grouped = df_filtered.groupby("계약종별")[month_order].sum().T
grouped.index.name = "월"
grouped.reset_index(inplace=True)
grouped["월"] = pd.Categorical(grouped["월"], categories=month_order, ordered=True)
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
