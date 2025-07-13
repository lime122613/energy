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

# ✅ 시도 선택
st.title("시도별 계약종별 전력 사용량 비교")
sido_list = sorted(df["시도"].unique())
selected_sido = st.selectbox("시도를 선택하세요", sido_list)

# ✅ 선택한 시도의 계약종별 목록
filtered_df = df[df["시도"] == selected_sido]
contract_types = filtered_df["계약종별"].unique().tolist()

selected_contracts = st.multiselect(
    "비교할 계약종을 선택하세요",
    options=contract_types,
    default=contract_types[:1]  # 기본 1개 선택
)

# ✅ 꺾은선 그래프 시각화
st.subheader(f"{selected_sido}의 계약종별 월별 전력 사용량 비교")

if selected_contracts:
    line_data = filtered_df[filtered_df["계약종별"].isin(selected_contracts)]
    line_data_grouped = line_data.groupby("계약종별")[month_columns].sum().T
    line_data_grouped.index.name = "월"
    line_data_grouped.reset_index(inplace=True)

    # 월 텍스트 정렬
    line_data_grouped["월"] = pd.Categorical(line_data_grouped["월"], categories=month_columns, ordered=True)

    line_df_melted = line_data_grouped.melt(id_vars="월", var_name="계약종별", value_name="전력사용량")

    fig = px.line(
        line_df_melted,
        x="월",
        y="전력사용량",
        color="계약종별",
        markers=True,
        title=f"{selected_sido}의 계약종별 월별 전력 사용량"
    )
    st.plotly_chart(fig)
else:
    st.warning("최소 하나의 계약종을 선택해주세요.")
