import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="주식 비교 봇", layout="wide")
st.title("주식 비교 봇")
st.write("종목코드를 쉼표로 입력하세요. 예: AAPL, MSFT, NVDA, 005930.KS")

symbols_input = st.text_input(
    "종목코드 입력",
    value="AAPL, MSFT, NVDA, 005930.KS"
)

# -----------------------------
# 유틸 함수
# -----------------------------
def is_korean_stock(symbol):
    return symbol.endswith(".KS") or symbol.endswith(".KQ")

def format_price(value, symbol):
    if value is None or pd.isna(value):
        return "-"
    try:
        if is_korean_stock(symbol):
            return f"{value:,.0f}원"
        else:
            return f"${value:,.2f}"
    except:
        return str(value)

def format_number(value, digits=2):
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{value:,.{digits}f}"
    except:
        return str(value)

def format_percent(value):
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{value * 100:.2f}%"
    except:
        return str(value)

def format_dividend_yield(value):
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{value * 100:.2f}%"
    except:
        return str(value)

def format_drop_percent(value):
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{value:.2f}%"
    except:
        return str(value)

def format_market_cap(value, symbol):
    if value is None or pd.isna(value):
        return "-"
    try:
        if is_korean_stock(symbol):
            return f"{value / 1_0000_0000_0000:.2f}조 원"
        else:
            return f"${value / 1_000_000_000:.2f}B"
    except:
        return str(value)

def format_ebitda(value, symbol):
    if value is None or pd.isna(value):
        return "-"
    try:
        if is_korean_stock(symbol):
            return f"{value / 1_0000_0000_0000:.2f}조 원"
        else:
            return f"${value / 1_000_000_000:.2f}B"
    except:
        return str(value)

# -----------------------------
# 핵심 데이터 함수 (안정 구조)
# -----------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):
    ticker = yf.Ticker(symbol)

    # 기본 구조 (절대 깨지지 않음)
    data = {
        "종목명": symbol,
        "종목코드": symbol,
        "통화": "KRW" if is_korean_stock(symbol) else "USD",

        "52주 최고가": "-",
        "52주 최저가": "-",
        "최고가대비하락률": "-",
        "평가금액": "-",

        "PER": "-",
        "EPS": "-",
        "시가총액": "-",
        "PBR": "-",
        "BPS": "-",
        "ROA": "-",
        "ROE": "-",
        "EV/EBITDA": "-",
        "EBITDA": "-",
        "배당금": "-",
        "배당율": "-"
    }

    # -----------------------------
    # 1️⃣ 안정 데이터 (가격)
    # -----------------------------
    try:
        hist = ticker.history(period="1y")

        if not hist.empty:
            current_price = hist["Close"].iloc[-1]
            high_52 = hist["High"].max()
            low_52 = hist["Low"].min()

            drop = ((high_52 - current_price) / high_52) * 100 if high_52 else None

            data.update({
                "평가금액": format_price(current_price, symbol),
                "52주 최고가": format_price(high_52, symbol),
                "52주 최저가": format_price(low_52, symbol),
                "최고가대비하락률": format_drop_percent(drop),
            })
    except:
        pass

    # -----------------------------
    # 2️⃣ 보조 데이터 (재무)
    # -----------------------------
    try:
        info = ticker.get_info()

        data.update({
            "종목명": info.get("longName") or info.get("shortName") or symbol,
            "PER": format_number(info.get("trailingPE")),
            "EPS": format_price(info.get("trailingEps"), symbol),
            "시가총액": format_market_cap(info.get("marketCap"), symbol),
            "PBR": format_number(info.get("priceToBook")),
            "BPS": format_price(info.get("bookValue"), symbol),
            "ROA": format_percent(info.get("returnOnAssets")),
            "ROE": format_percent(info.get("returnOnEquity")),
            "EV/EBITDA": format_number(info.get("enterpriseToEbitda")),
            "EBITDA": format_ebitda(info.get("ebitda"), symbol),
            "배당금": format_price(info.get("dividendRate"), symbol),
            "배당율": format_dividend_yield(info.get("dividendYield")),
        })
    except:
        pass

    return data

# -----------------------------
# 실행
# -----------------------------
if st.button("조회"):
    symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
    rows = []

    with st.spinner("데이터 불러오는 중..."):
        for symbol in symbols:
            rows.append(get_stock_data(symbol))

    df = pd.DataFrame(rows)

    st.subheader("조회 결과")

    display_columns = [
        "종목명", "종목코드", "통화",
        "52주 최고가", "52주 최저가", "최고가대비하락률",
        "평가금액", "PER", "EPS", "시가총액", "PBR", "BPS",
        "ROA", "ROE", "EV/EBITDA", "EBITDA", "배당금", "배당율"
    ]

    st.dataframe(df[display_columns], use_container_width=True)

    # -----------------------------
    # 정렬 기능
    # -----------------------------
    if "ROE" in df.columns:
        st.subheader("ROE 높은 순")
        st.dataframe(df.sort_values("ROE", ascending=False), use_container_width=True)

    if "PER" in df.columns:
        st.subheader("PER 낮은 순")
        st.dataframe(df.sort_values("PER", ascending=True), use_container_width=True)
