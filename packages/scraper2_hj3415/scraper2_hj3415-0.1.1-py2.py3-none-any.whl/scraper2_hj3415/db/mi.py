from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from utils_hj3415 import setup_logger


mylogger = setup_logger(__name__, 'WARNING')


DATE_FORMAT = "%Y.%m.%d"
DB_NAME = 'mi'

async def save(data: dict[str, dict], client: AsyncIOMotorClient):
    db = client[DB_NAME]
    for collection_name, doc in data.items():
        try:
            date_str = doc.get("날짜")
            if not date_str:
                print(f"{collection_name}: 날짜 없음, 저장 건너뜀")
                continue
            date_obj = datetime.strptime(date_str, DATE_FORMAT)
            doc["날짜"] = date_obj
            mylogger.debug(f"{collection_name} - 원본 날짜 문자열:", date_str)

            collection = db[collection_name]
            await collection.create_index("날짜", unique=True)

            result = await collection.update_one(
                {"날짜": date_obj},
                {"$set": doc},
                upsert=True
            )
            status = "삽입" if result.upserted_id else "업데이트"
            print(f"{collection_name}: {status}")
        except Exception as e:
            print(f"{collection_name}: 오류 - {e}")


async def find(col: str, date_str: str, client: AsyncIOMotorClient):
    db = client[DB_NAME]
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    collection = db[col]
    doc = await collection.find_one({"날짜": date_obj})
    mylogger.debug(f"{col} 날짜 타입 확인:", doc["날짜"], repr(doc["날짜"]))
    if doc:
        print(f"조회 결과 ({col}): {doc}")
    else:
        print(f"{col} 컬렉션에 {date_str} 날짜 데이터 없음")


async def delete(col: str, date_str: str, client: AsyncIOMotorClient):
    db = client["mi"]
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    collection = db[col]
    result = await collection.delete_one({"날짜": date_obj})
    if result.deleted_count > 0:
        print(f"{col}: {date_str} 데이터 삭제 완료")
    else:
        print(f"{col}: 삭제할 데이터 없음")
