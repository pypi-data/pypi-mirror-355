from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, UpdateOne
from scraper2_hj3415.db.nfs.base import *

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')


async def save(code: str, data: pd.DataFrame, client: AsyncIOMotorClient) -> dict:
    if data is None or data.empty:
        print("데이터 없음 - 저장 생략")
        return {"status": "unchanged"}

    db = client[DB_NAME]
    collection = db["c108"]

    await collection.create_index(
        [("코드", ASCENDING), ("날짜", ASCENDING), ("제목", ASCENDING)],
        unique=True
    )

    # NaN -> None 변환
    df = data.where(pd.notnull(data), None)
    operations = []
    inserted, updated, skipped = 0, 0, 0

    for _, row in df.iterrows():
        try:
            date_str = row["날짜"]
            date_obj = datetime.strptime(date_str, "%Y.%m.%d").replace(tzinfo=timezone.utc)

            doc = row.to_dict()
            doc["코드"] = code
            doc["날짜"] = date_obj

            filter_ = {"코드": code, "날짜": date_obj, "제목": doc["제목"]}
            operations.append(UpdateOne(filter_, {"$set": doc}, upsert=True))
        except Exception as e:
            print(f"변환 에러 - {row.get('제목', '제목 없음')}: {e}")
            continue

    if operations:
        result = await collection.bulk_write(operations, ordered=False)
        inserted = result.upserted_count
        updated = result.modified_count
        print(f"[{code}] 저장 완료: inserted={inserted}, updated={updated}")
    else:
        print(f"[{code}] 저장할 작업 없음")

    return {"inserted": inserted, "updated": updated}


async def save_many(many_data: dict[str, pd.DataFrame], client: AsyncIOMotorClient) -> dict:
    total_result = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

    for code, df in many_data.items():
        if df is None:
            print(f"[{code}] 리포트 없음 - 건너뜀")
            continue

        try:
            result = await save(code, df, client)
            total_result["inserted"] += result.get("inserted", 0)
            total_result["updated"] += result.get("updated", 0)
            total_result["skipped"] += result.get("skipped", 0)
        except Exception as e:
            print(f"[{code}] 저장 실패: {e}")
            total_result["errors"].append({"code": code, "error": str(e)})

    return total_result


