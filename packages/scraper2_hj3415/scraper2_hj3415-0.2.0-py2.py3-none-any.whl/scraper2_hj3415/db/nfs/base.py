from datetime import datetime, timezone
import pandas as pd
import json
from deepdiff import DeepDiff
from motor.motor_asyncio import AsyncIOMotorClient

DATE_FORMAT = "%Y.%m.%d"
DB_NAME = "nfs"


def prepare_c101_document(doc: dict) -> dict | None:
    code = doc.get("코드")
    date_str = doc.get("날짜")

    if not code or not date_str:
        print(f"코드 또는 날짜 누락: {code} / {date_str}")
        return None

    try:
        doc["날짜"] = datetime.strptime(date_str, DATE_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"날짜 형식 오류 - 건너뜀: {code} / {date_str}")
        return None

    return doc


def generate_c10346_document(code: str, data: dict[str, pd.DataFrame]) -> dict:
    now = datetime.now(timezone.utc)
    document = {"코드": code, "날짜": now}
    for page, df in data.items():
        if isinstance(df, pd.DataFrame):
            document[page] = df.where(pd.notnull(df), None).to_dict(orient="records")
    return document


async def compare_and_log_diff(db, code: str, new_doc: dict, latest_doc: dict | None) -> bool:
    if not latest_doc:
        return True

    latest_doc.pop("_id", None)
    latest_doc.pop("날짜", None)
    new_copy = dict(new_doc)
    new_copy.pop("날짜", None)

    diff = DeepDiff(latest_doc, new_copy, ignore_order=True)
    if not diff:
        print(f"{code} 기존 문서와 동일 - 저장하지 않음")
        return False

    print("변경된 항목:")
    for change_type, changes in diff.items():
        print(f"- {change_type}:")
        for path, value in changes.items():
            print(f"  {path}: {value}")

    await db["change_log"].insert_one({
        "코드": code,
        "변경시각": datetime.now(timezone.utc),
        "변경내용": json.loads(diff.to_json())
    })

    return True


async def get_all_codes(client: AsyncIOMotorClient) -> list[str]:
    db = client[DB_NAME]

    collections = ['c103', 'c104', 'c106']

    # 첫 컬렉션으로 초기화
    s = set(await db[collections[0]].distinct("코드"))

    for col in collections[1:]:
        codes = await db[col].distinct("코드")
        s &= set(codes)

    return list(s)


async def delete_code_from_all_collections(code: str, client: AsyncIOMotorClient) -> dict[str, int]:
    db = client[DB_NAME]

    collections = ['c101', 'c103', 'c104', 'c106', 'c108']

    deleted_counts = {}

    for col in collections:
        result = await db[col].delete_many({"코드": code})
        deleted_counts[col] = result.deleted_count

    print(f"삭제된 도큐먼트 갯수: {deleted_counts}")
    return deleted_counts

