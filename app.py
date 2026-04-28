import streamlit as st
import pandas as pd
import yfinance as yf
from pykrx import stock
from datetime import datetime, timedelta

st.set_page_config(page_title="주식 비교 봇", layout="wide")
st.title("주식 비교 봇")
st.write("종목코드를 쉼표로 입력하세요. 예: AAPL, MSFT, NVDA, 005930.KS, 000660.KS")

symbols_input = st.text_input(
    "종목코드 입력",
    value="AAPL, MSFT, NVDA, 005930.KS"
)

def is_korean_stock(symbol):
    return symbol.endswith(".KS") or symbol.endswith(".KQ")

def clean_krx_symbol(symbol):
    return symbol.replace(".KS", "").replace(".KQ", "")

def get_stock_name(symbol, info=None):
    try:
        if is_korean_stock(symbol):
            ticker = clean_krx_symbol(symbol)
            name = stock.get_market_ticker_name(ticker)
            return name if name else symbol
        else:
            if info is None:
                info = yf.Ticker(symbol).info
            return info.get("longName") or info.get("shortName") or symbol
    except:
        return symbol

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
        return f"{value:.2f}%"
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
            if value >= 1_0000_0000_0000:
                return f"{value / 1_0000_0000_0000:.2f}조 원"
            elif value >= 1_0000_0000:
                return f"{value / 1_0000_0000:.2f}억 원"
            else:
                return f"{value:,.0f}원"
        else:
            if value >= 1_000_000_000_000:
                return f"${value / 1_000_000_000_000:.2f}T"
            elif value >= 1_000_000_000:
                return f"${value / 1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"${value / 1_000_000:.2f}M"
            else:
                return f"${value:,.0f}"
    except:
        return str(value)

def format_ebitda(value, symbol):
    if value is None or pd.isna(value):
        return "-"
    try:
        if is_korean_stock(symbol):
            if value >= 1_0000_0000_0000:
                return f"{value / 1_0000_0000_0000:.2f}조 원"
            elif value >= 1_0000_0000:
                return f"{value / 1_0000_0000:.2f}억 원"
            else:
                return f"{value:,.0f}원"
        else:
            if value >= 1_000_000_000_000:
                return f"${value / 1_000_000_000_000:.2f}T"
            elif value >= 1_000_000_000:
                return f"${value / 1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"${value / 1_000_000:.2f}M"
            else:
                return f"${value:,.0f}"
    except:
        return str(value)

def get_kr_52week_range(ticker):
    end = datetime.today()
    start = end - timedelta(days=370)

    df = stock.get_market_ohlcv_by_date(
        start.strftime("%Y%m%d"),
        end.strftime("%Y%m%d"),
        ticker,
        adjusted=False
    )

    if df.empty:
        return None, None, None

    current_price = df["종가"].iloc[-1]
    high_52 = df["고가"].max()
    low_52 = df["저가"].min()

    return current_price, high_52, low_52

def get_korean_stock_data(symbol):
    ticker = clean_krx_symbol(symbol)

    try:
        current_price, high_52, low_52 = get_kr_52week_range(ticker)
    except:
        current_price, high_52, low_52 = None, None, None

    yf_ticker = yf.Ticker(symbol)
    info = yf_ticker.info
    stock_name = get_stock_name(symbol, info)

    if current_price is None:
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    if high_52 is None:
        high_52 = info.get("fiftyTwoWeekHigh")

    if low_52 is None:
        low_52 = info.get("fiftyTwoWeekLow")

    drop_from_high = None
    if current_price is not None and high_52 not in [None, 0]:
        drop_from_high = ((high_52 - current_price) / high_52) * 100

    return {
        "종목명": stock_name,
        "종목코드": symbol,
        "통화": "KRW",

        "52주 최고가_raw": high_52,
        "52주 최저가_raw": low_52,
        "최고가대비하락률_raw": drop_from_high,
        "평가금액_raw": current_price,
        "PER_raw": info.get("trailingPE"),
        "EPS_raw": info.get("trailingEps"),
        "시가총액_raw": info.get("marketCap"),
        "PBR_raw": info.get("priceToBook"),
        "BPS_raw": info.get("bookValue"),
        "ROA_raw": info.get("returnOnAssets"),
        "ROE_raw": info.get("returnOnEquity"),
        "EV/EBITDA_raw": info.get("enterpriseToEbitda"),
        "EBITDA_raw": info.get("ebitda"),
        "배당금_raw": info.get("dividendRate"),
        "배당율_raw": info.get("dividendYield"),

        "52주 최고가": format_price(high_52, symbol),
        "52주 최저가": format_price(low_52, symbol),
        "최고가대비하락률": format_drop_percent(drop_from_high),
        "평가금액": format_price(current_price, symbol),
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
    }

def get_us_stock_data(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    stock_name = get_stock_name(symbol, info)

    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    high_52 = info.get("fiftyTwoWeekHigh")
    low_52 = info.get("fiftyTwoWeekLow")

    drop_from_high = None
    if current_price is not None and high_52 not in [None, 0]:
        drop_from_high = ((high_52 - current_price) / high_52) * 100

    return {
        "종목명": stock_name,
        "종목코드": symbol,
        "통화": "USD",

        "52주 최고가_raw": high_52,
        "52주 최저가_raw": low_52,
        "최고가대비하락률_raw": drop_from_high,
        "평가금액_raw": current_price,
        "PER_raw": info.get("trailingPE"),
        "EPS_raw": info.get("trailingEps"),
        "시가총액_raw": info.get("marketCap"),
        "PBR_raw": info.get("priceToBook"),
        "BPS_raw": info.get("bookValue"),
        "ROA_raw": info.get("returnOnAssets"),
        "ROE_raw": info.get("returnOnEquity"),
        "EV/EBITDA_raw": info.get("enterpriseToEbitda"),
        "EBITDA_raw": info.get("ebitda"),
        "배당금_raw": info.get("dividendRate"),
        "배당율_raw": info.get("dividendYield"),

        "52주 최고가": format_price(high_52, symbol),
        "52주 최저가": format_price(low_52, symbol),
        "최고가대비하락률": format_drop_percent(drop_from_high),
        "평가금액": format_price(current_price, symbol),
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
    }

if st.button("조회"):
    symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
    rows = []

    for symbol in symbols:
        try:
            if is_korean_stock(symbol):
                rows.append(get_korean_stock_data(symbol))
            else:
                rows.append(get_us_stock_data(symbol))
        except Exception as e:
            rows.append({
                "종목명": symbol,
                "종목코드": symbol,
                "오류": str(e)
            })

    df = pd.DataFrame(rows)

    st.subheader("조회 결과")

    display_columns = [
        "종목명", "종목코드", "통화", "52주 최고가", "52주 최저가", "최고가대비하락률",
        "평가금액", "PER", "EPS", "시가총액", "PBR", "BPS",
        "ROA", "ROE", "EV/EBITDA", "EBITDA", "배당금", "배당율"
    ]

    existing_display_columns = [col for col in display_columns if col in df.columns]
    st.dataframe(df[existing_display_columns], use_container_width=True)

    if "ROE_raw" in df.columns:
        st.subheader("ROE 높은 순")
        sorted_df = df.sort_values("ROE_raw", ascending=False, na_position="last")
        st.dataframe(sorted_df[existing_display_columns], use_container_width=True)

    if "PER_raw" in df.columns:
        st.subheader("PER 낮은 순")
        sorted_df = df.sort_values("PER_raw", ascending=True, na_position="last")
        st.dataframe(sorted_df[existing_display_columns], use_container_width=True)

    if "최고가대비하락률_raw" in df.columns:
        st.subheader("최고가 대비 하락률 큰 순")
        sorted_df = df.sort_values("최고가대비하락률_raw", ascending=False, na_position="last")
        st.dataframe(sorted_df[existing_display_columns], use_container_width=True)