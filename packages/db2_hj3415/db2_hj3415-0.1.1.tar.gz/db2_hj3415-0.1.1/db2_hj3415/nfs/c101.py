from pymongo import ASCENDING, UpdateOne, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import pandas as pd

from db2_hj3415.nfs import DATE_FORMAT, DB_NAME
from db2_hj3415.common.db_ops import get_collection
from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')

COL_NAME = "c101"

def _prepare_c101_document(doc: dict) -> dict | None:
    """
    C101 컬렉션에 저장할 문서를 사전 처리합니다.

    - '코드'와 '날짜' 필드가 없으면 None을 반환합니다.
    - '날짜' 필드는 UTC 타임존을 포함한 datetime 객체로 변환합니다.
    - 날짜 형식이 잘못된 경우 None을 반환합니다.

    Parameters:
        doc (dict): 원시 입력 문서 (예: 스크래핑 또는 파싱 결과)

    Returns:
        dict | None: 정상적으로 처리된 문서 또는 오류 시 None
    """
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


async def save(data: dict | None, client: AsyncIOMotorClient) -> dict:
    if not data:
        print("데이터 없음 - 저장 생략")
        return {"status": "unchanged"}

    collection = get_collection(client, DB_NAME, COL_NAME)
    await collection.create_index([("날짜", ASCENDING), ("코드", ASCENDING)], unique=True)

    doc = _prepare_c101_document(data)
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
    collection = get_collection(client, DB_NAME, COL_NAME)
    await collection.create_index([("날짜", ASCENDING), ("코드", ASCENDING)], unique=True)

    operations = []
    inserted, updated, skipped = 0, 0, 0
    for code, doc in many_data.items():
        if not doc:
            print(f"{code}: 데이터 없음 - 건너뜀")
            continue

        doc = _prepare_c101_document(doc)
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
    collection = get_collection(client, DB_NAME, COL_NAME)
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
    collection = get_collection(client, DB_NAME, COL_NAME)
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

