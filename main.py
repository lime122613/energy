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

