import streamlit as st
import pandas as pd
import yfinance as yf

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
    return f"{value:,.0f}원" if is_korean_stock(symbol) else f"${value:,.2f}"

def format_number(value):
    if value is None or pd.isna(value):
        return "-"
    return f"{value:,.2f}"

def format_percent(value):
    if value is None or pd.isna(value):
        return "-"
    return f"{value * 100:.2f}%"

def format_drop_percent(value):
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.2f}%"

# -----------------------------
# 핵심 데이터 함수
# -----------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):
    ticker = yf.Ticker(symbol)

    data = {
        "종목명": symbol,
        "종목코드": symbol,
        "통화": "KRW" if is_korean_stock(symbol) else "USD",

        "평가금액": "-",
        "52주 최고가": "-",
        "52주 최저가": "-",
        "최고가대비하락률": "-",

        "PER": "-",
        "EPS": "-",
        "PBR": "-",
        "BPS": "-",
        "ROE": "-",
        "시가총액": "-"
    }

    price = None  # 계산용

    # -----------------------------
    # 1️⃣ 가격 데이터 (안정)
    # -----------------------------
    try:
        hist = ticker.history(period="1y")

        if not hist.empty:
            price = hist["Close"].iloc[-1]
            high = hist["High"].max()
            low = hist["Low"].min()

            drop = ((high - price) / high) * 100 if high else None

            data.update({
                "평가금액": format_price(price, symbol),
                "52주 최고가": format_price(high, symbol),
                "52주 최저가": format_price(low, symbol),
                "최고가대비하락률": format_drop_percent(drop),
            })
    except:
        pass

    # -----------------------------
    # 2️⃣ 재무 데이터 (직접 계산)
    # -----------------------------
    try:
        fin = ticker.financials
        bs = ticker.balance_sheet
        fast = ticker.fast_info

        if not fin.empty and not bs.empty:
            net_income = fin.loc["Net Income"].iloc[0]
            equity = bs.loc["Total Stockholder Equity"].iloc[0]

            shares = fast.get("shares")

            if shares and price:
                eps = net_income / shares
                bps = equity / shares

                data["EPS"] = format_price(eps, symbol)
                data["BPS"] = format_price(bps, symbol)

                if eps != 0:
                    data["PER"] = format_number(price / eps)

                if bps != 0:
                    data["PBR"] = format_number(price / bps)

            if equity != 0:
                data["ROE"] = format_percent(net_income / equity)

        # 시총
        if fast.get("market_cap"):
            mc = fast.get("market_cap")
            data["시가총액"] = (
                f"{mc/1_0000_0000_0000:.2f}조원"
                if is_korean_stock(symbol)
                else f"${mc/1_000_000_000:.2f}B"
            )

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
        "평가금액", "52주 최고가", "52주 최저가", "최고가대비하락률",
        "PER", "EPS", "PBR", "BPS", "ROE", "시가총액"
    ]

    st.dataframe(df[display_columns], use_container_width=True)

    # -----------------------------
    # 정렬
    # -----------------------------
    try:
        df_numeric = df.copy()
        df_numeric["ROE_num"] = df["ROE"].str.replace("%", "").astype(float)

        st.subheader("ROE 높은 순")
        st.dataframe(df_numeric.sort_values("ROE_num", ascending=False)[display_columns])
    except:
        pass

    try:
        df_numeric["PER_num"] = df["PER"].astype(float)

        st.subheader("PER 낮은 순")
        st.dataframe(df_numeric.sort_values("PER_num")[display_columns])
    except:
        pass
