from pymongo import UpdateOne
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient

from utils_hj3415 import setup_logger


mylogger = setup_logger(__name__, 'WARNING')


DATE_FORMAT = "%Y.%m.%d"
DB_NAME = 'mi'

async def save_market_history_type1(df: pd.DataFrame, market: str, numeric_columns: list | None, client: AsyncIOMotorClient):
    if df.empty:
        print("빈 데이터프레임입니다.")
        return {"inserted": 0, "updated": 0}

    db = client[DB_NAME]
    collection = db[market]

    # 컬럼 정리
    df.columns = df.columns.str.strip()

    # 날짜 파싱
    try:
        df["날짜"] = pd.to_datetime(df["날짜"], format=DATE_FORMAT, utc=True)
    except Exception as e:
        print(f"날짜 파싱 실패: {e}")
        return {"inserted": 0, "updated": 0}

    # 숫자형 변환
    if numeric_columns:
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    # dict 변환
    records = df.to_dict(orient="records")

    # 인덱스 (1회만)
    await collection.create_index("날짜", unique=True)

    # upsert 준비
    operations = []
    for r in records:
        if "날짜" not in r:
            print("날짜 필드 없음 - 건너뜀:", r)
            continue
        operations.append(UpdateOne({"날짜": r["날짜"]}, {"$set": r}, upsert=True))

    # 실행
    if operations:
        result = await collection.bulk_write(operations)
        print(f"{market}: upsert 완료 - 삽입 {result.upserted_count}, 수정 {result.modified_count}")
        return {"inserted": result.upserted_count, "updated": result.modified_count}
    else:
        print("실행할 작업이 없습니다.")
        return {"inserted": 0, "updated": 0}


async def save_sp500_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'sp500'
    numeric_columns = ["종가", "전일대비", "시가", "고가", "저가"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_kospi_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'kospi'
    numeric_columns = ["체결가", "전일비", "거래량(천주)", "거래대금(백만)"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_kosdaq_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'kosdaq'
    numeric_columns = ["체결가", "전일비", "거래량(천주)", "거래대금(백만)"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_wti_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'wti'
    numeric_columns = ["종가", "전일대비"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_usdkrw_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'udskrw'
    numeric_columns = ["매매기준율", "전일대비", "현찰로 사실 때", "현찰로 파실 때", "송금 보내실 때", "송금 받으실 때"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_silver_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'silver'
    numeric_columns = ["종가", "전일대비"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_gold_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'gold'
    numeric_columns = ["종가", "전일대비"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_gbond3y_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'gbond3y'
    numeric_columns = ["종가", "전일대비"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_chf_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'chf'
    numeric_columns = ["종가", "전일대비"]
    await save_market_history_type1(df, market, numeric_columns, client)


async def save_aud_history(df: pd.DataFrame, client: AsyncIOMotorClient):
    market = 'aud'
    numeric_columns = ["종가", "전일대비"]
    await save_market_history_type1(df, market, numeric_columns, client)


