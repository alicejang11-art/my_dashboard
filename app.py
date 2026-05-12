import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────
# 기본 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="한국인 해외취업 분석 대시보드",
    page_icon="🌏",
    layout="wide",
)

st.title("🌏 한국인 해외취업 공공데이터 분석 대시보드")
st.caption("데이터 출처: 해외취업.db (SQLite) | 청년실업률 · 해외취업통계 · 구인처 정보")

# ──────────────────────────────────────────
# DB 연결 함수 (캐시 적용 → 속도 향상)
# ──────────────────────────────────────────
@st.cache_resource
def get_connection():
    """SQLite DB에 연결하고 커넥션 객체를 반환합니다."""
    return sqlite3.connect("해외취업.db", check_same_thread=False)

@st.cache_data
def run_query(sql: str) -> pd.DataFrame:
    """SQL을 실행하고 DataFrame으로 반환합니다."""
    conn = get_connection()
    return pd.read_sql_query(sql, conn)

conn = get_connection()

# ──────────────────────────────────────────
# 사이드바 — 연도 필터
# ──────────────────────────────────────────
with st.sidebar:
    st.header("🔧 필터")
    year_df = run_query("SELECT MIN(연도) AS min_y, MAX(연도) AS max_y FROM 해외취업연도별통계")
    min_year = int(year_df["min_y"].iloc[0])
    max_year = int(year_df["max_y"].iloc[0])
    year_range = st.slider(
        "분석 연도 범위",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
    )
    st.markdown("---")
    st.info("차트 아래 'SQL 보기'를 펼치면\n사용된 쿼리를 확인할 수 있습니다.")

start_y, end_y = year_range

# ──────────────────────────────────────────
# 차트 1: 연도별 국가별 한국인 해외취업 수 (라인 차트)
# ──────────────────────────────────────────
st.markdown("---")
st.subheader("📈 Chart 1 · 연도별 국가별 한국인 해외취업 수")

SQL1 = f"""
SELECT 연도, 미국, 일본, 싱가포르, 호주, 아랍에미리트, 중국, 캐나다, 베트남, 인도네시아, 독일, 기타
FROM   해외취업연도별통계
WHERE  연도 BETWEEN {start_y} AND {end_y}
ORDER  BY 연도
"""
df1 = run_query(SQL1)

# wide → long 변환 (Plotly가 선호하는 형태)
df1_long = df1.melt(id_vars="연도", var_name="국가", value_name="취업자수")

fig1 = px.line(
    df1_long,
    x="연도", y="취업자수", color="국가",
    markers=True,
    title="연도별 국가별 한국인 해외취업자 수",
    labels={"취업자수": "취업자 수 (명)", "연도": "연도"},
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig1.update_layout(hovermode="x unified", legend_title_text="국가")
st.plotly_chart(fig1, use_container_width=True)

with st.expander("🔍 사용한 SQL 보기"):
    st.code(SQL1, language="sql")

st.info(
    "💡 **인사이트**\n"
    "- 국가별 해외취업 규모 차이가 뚜렷하게 나타났으며, 미국·일본 중심으로 해외취업이 집중되는 경향이 확인되었습니다.\n"
    "- 반면 중국은 한·중 관계 변화와 맞물려 특정 시점(2017년) 이후 감소 흐름이 관찰됩니다.\n"
    "- 코로나 시기인 2020~2021년에는 대부분 국가에서 해외취업 규모가 감소하는 흐름이 나타났으며, 특히 일본과 호주의 감소 폭이 상대적으로 크게 나타났습니다."
)

# ──────────────────────────────────────────
# 차트 2: 연도별 국가별 구인처 수 변화 (막대 차트)
# ──────────────────────────────────────────
st.markdown("---")
st.subheader("🏢 Chart 2 · 연도별 주요 국가 구인처 수 변화")

SQL2 = f"""
SELECT 연도, 국가, COUNT(*) AS 구인처수
FROM   구인처
WHERE  연도 BETWEEN {start_y} AND {end_y}
GROUP  BY 연도, 국가
ORDER  BY 연도, 구인처수 DESC
"""
df2 = run_query(SQL2)

# 상위 10개 국가만 필터링 (가독성)
top_countries = (
    df2.groupby("국가")["구인처수"].sum()
    .nlargest(10).index.tolist()
)
df2_top = df2[df2["국가"].isin(top_countries)]

fig2 = px.bar(
    df2_top,
    x="연도", y="구인처수", color="국가",
    barmode="group",
    title="연도별 주요 국가 구인처 수 (상위 10개국)",
    labels={"구인처수": "구인처 수 (개)", "연도": "연도"},
    color_discrete_sequence=px.colors.qualitative.Pastel,
)
fig2.update_layout(legend_title_text="국가")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("🔍 사용한 SQL 보기"):
    st.code(SQL2, language="sql")

st.info(
    "💡 **인사이트**\n"
    "- 일본은 대부분 연도에서 가장 많은 구인처 수를 기록했으며, 2018년 이후 다른 국가와의 격차가 더욱 확대되는 경향이 나타났습니다.\n"
    "  일본은 한국인 채용 수요가 구조적으로 가장 큰 시장임을 보여줍니다.\n"
    "- 베트남과 중국의 구인처 수는 2022년 이후 빠르게 증가했으며, 특히 베트남은 2023년에 가장 높은 증가 폭을 보입니다.\n"
    "- 국가별 구인처 수 변화 양상에는 차이가 존재했으며, 일부 국가는 구인처 수가 증가했음에도 해외취업 규모는 상대적으로 큰 변화를 보이지 않았습니다."
)

# ──────────────────────────────────────────
# 차트 3: 실업률 vs 한국인 해외취업자 수 (산점도)
# ──────────────────────────────────────────
st.markdown("---")
st.subheader("🔗 Chart 3 · 국가 실업률 vs 한국인 해외취업자 수 상관관계")

# 두 테이블을 연도 기준으로 JOIN 후 wide → long 변환
SQL3 = f"""
SELECT
    u.연도,
    u.미국    AS 미국_실업률,    e.미국    AS 미국_취업,
    u.일본    AS 일본_실업률,    e.일본    AS 일본_취업,
    u.싱가포르 AS 싱가포르_실업률, e.싱가포르 AS 싱가포르_취업,
    u.호주    AS 호주_실업률,    e.호주    AS 호주_취업,
    u.중국    AS 중국_실업률,    e.중국    AS 중국_취업,
    u.캐나다  AS 캐나다_실업률,  e.캐나다  AS 캐나다_취업,
    u.베트남  AS 베트남_실업률,  e.베트남  AS 베트남_취업,
    u.독일    AS 독일_실업률,    e.독일    AS 독일_취업,
    u.한국    AS 한국_실업률
FROM 청년실업률 u
JOIN 해외취업연도별통계 e ON u.연도 = e.연도
WHERE u.연도 BETWEEN {start_y} AND {end_y}
ORDER BY u.연도
"""
df3_raw = run_query(SQL3)

# 국가 목록을 직접 지정하여 long 형태로 변환
countries = ["미국", "일본", "싱가포르", "호주", "중국", "캐나다", "베트남", "독일"]
rows = []
for _, row in df3_raw.iterrows():
    for c in countries:
        rows.append({
            "연도": row["연도"],
            "국가": c,
            "청년실업률": row[f"{c}_실업률"],
            "해외취업자수": row[f"{c}_취업"],
        })
df3 = pd.DataFrame(rows).dropna()

fig3 = px.scatter(
    df3,
    x="청년실업률", y="해외취업자수",
    color="국가", size="해외취업자수",
    hover_data=["연도"],
    trendline="ols",
    trendline_scope="overall",
    title="국가별 실업률 vs 한국인 해외취업자 수",
    labels={"실업률": "실업률 (%)", "해외취업자수": "해외취업자 수 (명)"},
    color_discrete_sequence=px.colors.qualitative.Bold,
)
fig3.update_layout(legend_title_text="국가")
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔍 사용한 SQL 보기"):
    st.code(SQL3, language="sql")

st.info(
    "💡 **인사이트**\n"
    "- 전반적으로 현지 실업률이 낮은(고용 안정적인) 국가일수록 한국인 취업자 수가 많아지는 음의 상관관계가 나타나는 것처럼 보입니다.\n"
    "- 미국은 실업률 8에서 12% 구간에서도 500에서 1,600명대를 유지하며 추세선 예외 국가로, 실업률 외 요인(높은 임금, 영어권 선호)이 작용하고 있음을 시사합니다.\n"
    "- 결론적으로 한국인의 해외취업 국가 선택은 현지 실업률보다 임금 수준, 언어 장벽, 비자 정책, 산업 수요 등 구조적 요인에 더 크게 영향받는 것으로 해석됩니다."
)

# ──────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────
st.markdown("---")
st.caption("ⓒ 2025 해외취업 분석 대시보드 · Built with Streamlit & Plotly")
