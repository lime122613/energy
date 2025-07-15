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

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------
# 📊 전체 전력 사용량 기준 시도별 막대그래프
# --------------------------
st.title("전력 사용량 시각화 · 탐색 플랫폼")
st.header("🌍 전체 전력 사용량 기준 시도별 순위")

df_total_by_sido = df.groupby("시도")["연간총합"].sum().reset_index().sort_values(by="연간총합", ascending=False)

fig_total = px.bar(df_total_by_sido, x="시도", y="연간총합",
                   text="연간총합", labels={"연간총합": "전력 사용량 (kWh)", "시도": "지역"},
                   title="시도별 전체 전력 사용량 (연간)")
fig_total.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_total)

# --------------------------
# 🧩 시도별 계약종별 전력 사용 비율 (원그래프)
# --------------------------
st.header("🧩 시도별 계약종별 전력 사용 비율")

selected_pie_sido = st.selectbox("시도를 선택하세요", sorted(df["시도"].unique()), key="pie_select")

df_pie = df[df["시도"] == selected_pie_sido]
df_pie_grouped = df_pie.groupby("계약종별")["연간총합"].sum().reset_index()
df_pie_grouped = df_pie_grouped[df_pie_grouped["계약종별"] != "합계"]

fig_pie = px.pie(df_pie_grouped, names="계약종별", values="연간총합",
                 title=f"{selected_pie_sido} 계약종별 전력 사용 비율")
st.plotly_chart(fig_pie)

# --------------------------
# 📊 1. 계약종별 시도 전력 사용량 막대그래프
# --------------------------
st.title("전력 사용량 시각화 · 탐색 플랫폼")

st.header("📊 계약종별 시도 전력 사용량 비교")

selected_contract = st.selectbox("계약종을 선택하세요", contract_list)

df_grouped = df.groupby(["시도", "계약종별"])["연간총합"].sum().reset_index()
df_selected = df_grouped[df_grouped["계약종별"] == selected_contract].sort_values(by="연간총합", ascending=False)

# ✅ 사용량이 가장 높은 시도 찾기
top_region = df_selected.iloc[0]["시도"]
top_value = int(df_selected.iloc[0]["연간총합"])

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

# ✅ 학생 유도 메시지 및 선택지
message = f"💡 **{selected_contract}**의 경우 **{top_region}**의 연간 전력 사용량이 가장 높네요! " \
          f"{top_region}의 2024년 월별 전력 사용량을 좀 더 살펴볼까요?"


# --------------------------
# 📈 2. 시군구별 계약종 월별 사용량 꺾은선 그래프
# --------------------------
st.header("📈 시군구별 계약종 월별 사용량 비교")

selected_sido = st.selectbox("시도 선택", sorted(df["시도"].unique()))
available_sgg = sorted(df[df["시도"] == selected_sido]["시군구"].unique().tolist())

# ✔ 교육용이면 최대 사용량 기준 자동 선택
selected_contract = selected_contract  # 기존에 선택한 계약종
if selected_contract == "교육용":
    edu_df = df[(df["시도"] == selected_sido) & (df["계약종별"] == "교육용")]
    edu_df["총합"] = edu_df[month_columns].sum(axis=1)
    default_sgg = edu_df.sort_values(by="총합", ascending=False).iloc[0]["시군구"]
else:
    default_sgg = available_sgg[0]

selected_sgg = st.selectbox("시군구 선택", available_sgg, index=available_sgg.index(default_sgg))

# ✔ 필터링 및 합계 제외
df_filtered = df[
    (df["시도"] == selected_sido) &
    (df["시군구"] == selected_sgg) &
    (df["계약종별"] != "합계")
]

# ✔ 월 정렬
month_order = [f"{i}월" for i in range(1, 13)]

grouped = df_filtered.groupby("계약종별")[month_order].sum().T
grouped.index.name = "월"
grouped.reset_index(inplace=True)
grouped["월"] = pd.Categorical(grouped["월"], categories=month_order, ordered=True)

# ✔ 꺾은선 그래프 그리기
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

# ✔ 최고/최저 하이라이트
peak = melted.loc[melted["전력사용량"].idxmax()]
low = melted.loc[melted["전력사용량"].idxmin()]

st.success(f"✅ 최고 사용: **{peak['계약종별']}** - **{peak['월']}**에 **{int(peak['전력사용량']):,} kWh**")
st.info(f"🔻 최저 사용: **{low['계약종별']}** - **{low['월']}**에 **{int(low['전력사용량']):,} kWh**")
