from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient
import pprint
from scraper2_hj3415.db.nfs.base import *

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')


async def save(col: str, code: str, data: dict[str, pd.DataFrame], client: AsyncIOMotorClient) -> dict:
    db = client[DB_NAME]
    collection = db[col]

    await collection.create_index([("코드", ASCENDING), ("날짜", ASCENDING)], unique=True)

    document = generate_c10346_document(code, data)
    latest_doc = await collection.find_one({"코드": code}, sort=[("날짜", DESCENDING)])

    need_save = await compare_and_log_diff(db, code, document, latest_doc)
    if not need_save:
        return {"status": "unchanged"}

    result = await collection.insert_one(document)
    print(f"삽입됨:  {db.name}.{collection.name} / {code} (id={result.inserted_id})")
    del_result = await collection.delete_many({
        "_id": {"$in": [
            doc["_id"] for doc in await collection.find({"코드": code}).sort("날짜", DESCENDING).skip(2).to_list(length=None)
        ]}
    })
    print(f"삭제된 이전 문서 수: {del_result.deleted_count}")

    return {"status": "inserted", "id": str(result.inserted_id)}


async def save_many(col: str, many_data: dict[str, dict[str, pd.DataFrame]], client: AsyncIOMotorClient) -> list[dict]:
    db = client[DB_NAME]
    collection = db[col]
    await collection.create_index([("코드", ASCENDING), ("날짜", ASCENDING)], unique=True)

    results = []

    for code, data in many_data.items():
        document = generate_c10346_document(code, data)
        latest_doc = await collection.find_one({"코드": code}, sort=[("날짜", DESCENDING)])
        need_save = await compare_and_log_diff(db, code, document, latest_doc)

        if not need_save:
            results.append({"code": code, "status": "unchanged"})
            continue

        result = await collection.insert_one(document)
        await collection.delete_many({
            "_id": {"$in": [
                doc["_id"] for doc in await collection.find({"코드": code}).sort("날짜", DESCENDING).skip(2).to_list(length=None)
            ]}
        })

        results.append({"code": code, "status": "inserted", "id": str(result.inserted_id)})

    pprint.pprint(results)
    return results


async def get_latest(col: str, code: str, page: str, client: AsyncIOMotorClient) -> pd.DataFrame | None:
    db = client[DB_NAME]
    collection = db[col]

    # 최신 날짜 기준으로 정렬하여 1건만 조회
    latest_doc = await collection.find_one(
        {"코드": code},
        sort=[("날짜", DESCENDING)]
    )

    if not latest_doc or page not in latest_doc:
        print(f"문서 없음 또는 '{page}' 항목 없음")
        return None

        # records → DataFrame
    records = latest_doc[page]
    df = pd.DataFrame(records)
    return df


async def has_doc_changed(col: str, code: str, client: AsyncIOMotorClient) -> bool:
    db = client[DB_NAME]
    collection = db[col]

    # 최신 문서 2개 조회 (내림차순)
    docs = await collection.find({"코드": code}).sort("날짜", DESCENDING).limit(2).to_list(length=2)

    if len(docs) < 2:
        print(f"{code} 문서가 1개 이하임 - 비교 불가")
        return True  # 비교할 게 없으면 새로 저장해야 하므로 True

    new_doc, latest_doc = docs[0], docs[1]

    new_doc.pop("_id", None)
    new_doc.pop("날짜", None)
    latest_doc.pop("_id", None)
    latest_doc.pop("날짜", None)

    mylogger.debug(new_doc)
    mylogger.debug(latest_doc)

    # 비교 함수 호출
    return await compare_and_log_diff(db, code, new_doc, latest_doc)



