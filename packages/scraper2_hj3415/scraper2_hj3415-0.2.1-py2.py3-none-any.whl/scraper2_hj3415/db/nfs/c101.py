from pymongo import ASCENDING, UpdateOne, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient
from scraper2_hj3415.db.nfs.base import *

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')


async def save(data: dict | None, client: AsyncIOMotorClient) -> dict:
    if not data:
        print("데이터 없음 - 저장 생략")
        return {"status": "unchanged"}

    db = client[DB_NAME]
    collection = db["c101"]
    await collection.create_index([("날짜", ASCENDING), ("코드", ASCENDING)], unique=True)

    doc = prepare_c101_document(data)
    if not doc:
        return {"status": "unchanged"}

    filter_ = {"날짜": doc["날짜"], "코드": doc["코드"]}
    result = await collection.update_one(filter_, {"$set": doc}, upsert=True)
    if result.upserted_id:
        return {"status": f"upserted {result.upserted_id}"}
    elif result.modified_count:
        return {"status": f"modified"}
    else:
        return {"status": "unchanged"}


async def save_many(many_data: dict[str, dict | None], client: AsyncIOMotorClient) -> dict:
    db = client[DB_NAME]
    collection = db["c101"]
    await collection.create_index([("날짜", ASCENDING), ("코드", ASCENDING)], unique=True)

    operations = []
    inserted, updated, skipped = 0, 0, 0
    for code, doc in many_data.items():
        if not doc:
            print(f"{code}: 데이터 없음 - 건너뜀")
            continue

        doc = prepare_c101_document(doc)
        if not doc:
            continue

        filter_ = {"날짜": doc["날짜"], "코드": doc["코드"]}
        operations.append(UpdateOne(filter_, {"$set": doc}, upsert=True))

    if operations:
        result = await collection.bulk_write(operations)
        inserted = result.upserted_count
        updated = result.modified_count
        print(f"저장 완료: inserted={inserted}, updated={updated}")
    else:
        print(f"저장할 작업 없음")
    return {"inserted": inserted, "updated": updated}


async def get_latest(code: str, client: AsyncIOMotorClient) -> dict | None:
    db = client[DB_NAME]
    collection = db["c101"]

    doc = await collection.find_one(
        {"코드": code},
        sort=[("날짜", DESCENDING)]
    )

    if doc:
        doc.pop("_id", None)
        return doc
    else:
        print(f"데이터 없음: {code}")
        return None


async def get_all_as_df(code: str, client: AsyncIOMotorClient) -> pd.DataFrame | None:
    db = client[DB_NAME]
    collection = db["c101"]

    cursor = collection.find({"코드": code}).sort("날짜", ASCENDING)
    docs = await cursor.to_list(length=None)

    if not docs:
        print(f"[{code}] 관련 문서 없음")
        return None

    # _id 필드는 문자열로 변환하거나 제거
    for doc in docs:
        doc.pop("_id", None)

    df = pd.DataFrame(docs)
    return df

