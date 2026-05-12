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
    "- 일본의 독주가 두드러집니다. 2015년부터 구인처 수가 급증해 2018년 230여 곳으로 타 국가를 압도하며, 한국인 채용 수요가 구조적으로 가장 큰 시장임을 보여줍니다.\n"
    "- 반면 중국은 한·중 관계 변화와 맞물려 특정 시점 이후 뚜렷한 감소 흐름이 관찰됩니다.\n"
    "- 미국은 전통적 강세 국가이나, 비자 경쟁 심화로 증가 폭이 제한적입니다.\n"
    "- 코로나 시기에 해외 취업자 수가 급격히 감소하는 것을 확인할 수 있습니다."
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
    "- 구인처가 집중된 국가와 실제 취업자 수 상위 국가가 일치하는지 비교하면 수급 불균형 여부를 파악할 수 있습니다.\n"
    "- 특정 연도에 구인처가 급증한 국가는 정부의 MOU 체결 또는 현지 경기 회복과 연관될 가능성이 높습니다.\n"
    "- 구인처 수 대비 취업자 수 비율(전환율)을 추가 분석하면 실효성 높은 국가를 선별할 수 있습니다."
)

# ──────────────────────────────────────────
# 차트 3: 청년 실업률 vs 한국인 해외취업자 수 (산점도)
# ──────────────────────────────────────────
st.markdown("---")
st.subheader("🔗 Chart 3 · 국가 청년실업률 vs 한국인 해외취업자 수 상관관계")

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
    title="국가별 청년실업률 vs 한국인 해외취업자 수",
    labels={"청년실업률": "청년 실업률 (%)", "해외취업자수": "해외취업자 수 (명)"},
    color_discrete_sequence=px.colors.qualitative.Bold,
)
fig3.update_layout(legend_title_text="국가")
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔍 사용한 SQL 보기"):
    st.code(SQL3, language="sql")

st.info(
    "💡 **인사이트**\n"
    "- 전반적으로 현지 청년실업률이 낮은(고용 안정적인) 국가일수록 한국인 취업자 수도 많은 양의 상관관계가 나타납니다.\n"
    "- 단, 베트남처럼 실업률이 낮아도 임금 수준 차이로 취업자가 적은 '이상치' 국가가 존재합니다.\n"
    "- 추세선 기울기와 R² 값을 함께 보면 어느 국가군이 실업률-취업 수 연동성이 강한지 파악할 수 있습니다."
)

# ──────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────
st.markdown("---")
st.caption("ⓒ 2025 해외취업 분석 대시보드 · Built with Streamlit & Plotly")
